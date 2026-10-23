"""External IAM occurrences, saved placements, and moved-file resolution."""
import io
import math
import ntpath
import os
import re
import struct
from pathlib import Path
from uuid import UUID
import FreeCAD as App
from olefile import OleFileIO


class ReferenceReader:
    def __init__(self, data, offset=0):
        self.data, self.i = data, offset

    def take(self, n):
        if n < 0 or self.i + n > len(self.data):
            raise ValueError('Truncated Inventor reference table')
        value = self.data[self.i:self.i+n]
        self.i += n
        return value

    def integer(self, fmt='<I'):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def text(self):
        n = self.integer()
        if n > 32768:
            raise ValueError('Invalid Inventor reference string length')
        return self.take(n*2).decode('utf-16-le').rstrip('\0\n')

    def file(self):
        path = self.text()
        if ntpath.splitext(path)[1].lower() not in ('.ipt', '.iam') or '\0' in path:
            raise ValueError('Invalid Inventor component path')
        self.integer('<i')  # library ID
        self.text()        # library name
        self.integer('<H')
        if struct.unpack_from('<I', self.data, self.i)[0] & 0xFFFF0000:
            if self.integer('<H') != 0:
                raise ValueError('Invalid Inventor reference prefix')
        self.text()
        count = self.integer()
        if count > 10000:
            raise ValueError('Invalid Inventor reference array')
        self.take(count*6+4)
        identity = str(UUID(bytes_le=self.take(16))).upper()
        revision = str(UUID(bytes_le=self.take(16))).upper()
        identifier, occurrences, version, flags = (self.integer() for _ in range(4))
        if not 0 < identifier < 1000000 or occurrences > 1000000:
            raise ValueError('Invalid Inventor reference ID')
        return dict(path=path, identity=identity, revision=revision, id=identifier)


def references(data):
    """Locate and validate the complete counted UFRx file table.

    New UFRx LOD/model-state sections cannot be skipped by the old sequential
    parser. Only accept a count+caption+padding followed by all its file records;
    a path string by itself is never accepted as a component reference.
    """
    tables = []
    # The table caption may be empty or a short UTF-16 string.
    for start in range(len(data)-16):
        count, chars = struct.unpack_from('<II', data, start)
        if not 0 < count <= 10000 or chars > 256:
            continue
        first = start + 12 + chars*2
        if first+8 >= len(data):
            continue
        n = struct.unpack_from('<I', data, first)[0]
        if not 4 < n < 32768 or first+4+2*n > len(data):
            continue
        try:
            candidate = data[first+4:first+4+2*n].decode('utf-16-le').rstrip('\0\n')
            if not candidate.lower().endswith(('.ipt','.iam')):
                continue
            reader = ReferenceReader(data,start)
            reader.integer(); reader.text(); reader.integer()
            files = [reader.file() for _ in range(count)]
            if len({f['id'] for f in files}) != len(files):
                continue
            tables.append(files)
        except (ValueError, UnicodeError, struct.error):
            continue
    if len(tables) != 1:
        raise ValueError('Cannot identify a unique Inventor external file table')
    return tables[0]


def occurrences(model, refs):
    nodes = list(model.getDC().elementNodes.values())
    transforms = {}
    for n in nodes:
        if n.typeName == '216B3A55':
            key = tuple(n.get('lst0') or [])
            if len(key) == 1:
                transforms.setdefault(key[0], []).append(n.get('transformation'))
    result = []
    for node in nodes:
        if node.typeName != '90874D61':
            continue
        label = node.name or node.getName()
        stem = (label or '').rsplit(':',1)[0].casefold()
        matches = [r for r in refs if ntpath.splitext(ntpath.basename(r['path']))[0].casefold() == stem]
        if len(matches) != 1:
            raise ValueError('Ambiguous or unsupported IAM component reference: ' + str(label))
        value = node.get('value')
        identifier = value.get('u32_1') if value else None
        candidates = transforms.get(identifier, [])
        if len(candidates) != 1:
            raise ValueError('Missing or ambiguous IAM placement: ' + str(label))
        transform = candidates[0]
        m = transform.m
        matrix = App.Matrix(*[m[r][c] if c != 3 else (m[r][c]*10 if r<3 else 1) for r in range(4) for c in range(4)])
        if abs(matrix.determinant()-1) > 1e-6:
            raise ValueError('IAM occurrence has a non-rigid placement: ' + str(label))
        result.append(dict(label=label, reference=matches[0], placement=App.Placement(matrix), occurrence=identifier))
    if not result:
        raise ValueError('IAM contains no supported external occurrences')
    return result


def identity(path):
    from importerUFRxDoc import readHeader1
    with OleFileIO(str(path)) as ole:
        header, _ = readHeader1(ole.openstream('UFRxDoc').read(),0,io.StringIO())
    return dict(identity=str(header.name_ntrnl).upper(), revision=str(header.revision).upper(), original=header.fName)


def tokens(path):
    return sorted(t.casefold() for t in re.split(r'[_\s-]+', ntpath.splitext(ntpath.basename(str(path)))[0]) if t)


class Resolver:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.index = None

    def resolve(self, ref):
        expected = Path(ref['path'])
        basename = ntpath.basename(ref['path'])
        for path in (expected, self.directory / basename):
            if path.is_file():
                found = identity(path)
                if found['identity'] == ref['identity'] and found['revision'] == ref['revision']:
                    return path, found
        if self.index is None:
            self.index = []
            for folder, dirs, files in os.walk(str(self.directory)):
                dirs[:] = [d for d in dirs if d.lower() not in ('.git','__pycache__') and not d.lower().endswith(('_ipt','_iam'))]
                for name in files:
                    if Path(name).suffix.lower() not in ('.ipt','.iam'):
                        continue
                    path=Path(folder)/name
                    try:
                        self.index.append((path,identity(path)))
                    except (OSError, ValueError, KeyError, UnicodeError, struct.error):
                        continue
        same = [(p,meta) for p,meta in self.index if meta['identity'] == ref['identity']]
        for predicate in (
            lambda p,m: m['revision'] == ref['revision'],
            lambda p,m: 'oldversions' not in [x.lower() for x in p.parts] and ntpath.basename(m['original']).casefold() == basename.casefold(),
            lambda p,m: 'oldversions' not in [x.lower() for x in p.parts] and tokens(p.name) == tokens(basename),
        ):
            candidates = [(p,m) for p,m in same if predicate(p,m)]
            if len(candidates) == 1:
                return candidates[0]
            if len(candidates) > 1:
                raise ValueError('Ambiguous moved Inventor reference: ' + ref['path'])
        raise FileNotFoundError('Cannot resolve Inventor reference: ' + ref['path'])
