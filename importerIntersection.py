"""Recover surface intersections in place of coarse ACIS guide splines."""
import math
import FreeCAD as App
import Part
import Acis


def splineData(bsc):
    result = Acis.BS_Curve(bsc.isRational(), bsc.isPeriodic(), bsc.Degree)
    result.poles = bsc.getPoles()
    result.uMults = bsc.getMultiplicities()
    result.uKnots = bsc.getKnots()
    result.weights = bsc.getWeights()
    return result


def screwCylinderIntersection(curve,sources):
    """A circular screw sweep meets a coaxial cylinder in two exact helices."""
    if sum(isinstance(s,Acis.SurfaceCone) for s in sources)!=1 or sum(isinstance(s,Acis.SurfaceSpline) for s in sources)!=1:return None
    expanded=[s.getSurface() if isinstance(s,Acis.SurfaceSpline) else s for s in sources]
    cylinders=[s for s in expanded if isinstance(s,Acis.SurfaceCone)]
    sweeps=[s for s in expanded if isinstance(s,Acis.SurfaceSpline) and s.subtype=='sweep_spl_sur']
    if len(cylinders)!=1 or len(sweeps)!=1:return None
    cylinder,sweep=cylinders[0],sweeps[0]
    h=getattr(getattr(sweep,'path',None),'helix',None);profile=getattr(sweep,'profile',None)
    if h is None or profile is None or profile.__name__!='ellipse':return None
    if abs(cylinder.sine)>1e-12 or abs(cylinder.ratio-1)>1e-12 or abs(profile.ratio-1)>1e-12 or abs(h.facApex)>1e-12:return None
    radius=h.dirMajor.Length;other=h.dirMinor.Length
    if radius<=0 or abs(radius-other)>1e-9 or abs(h.dirMajor.dot(h.dirMinor))>1e-9:return None
    axis=h.dirMajor.cross(h.dirMinor).normalize()
    if abs(abs(App.Vector(cylinder.axis).normalize().dot(axis))-1)>1e-9:return None
    if abs(abs(App.Vector(profile.axis).normalize().dot(axis))-1)>1e-9:return None
    if (cylinder.center-h.posCenter).cross(axis).Length>1e-7 or h.dirPitch.cross(axis).Length>1e-7:return None
    pitch=h.dirPitch.dot(axis)
    if abs(pitch)<1e-12:return None
    lo=h.radAngles.getLowerLimit()
    center=h.posCenter+h.dirMajor*math.cos(lo)+h.dirMinor*math.sin(lo)
    if (profile.center-center).Length>1e-6:return None
    cr=cylinder.major.Length;pr=profile.major.Length
    if cr<=0 or pr<=0:return None
    cosine=(cr*cr+radius*radius-pr*pr)/(2*cr*radius)
    if not -1+1e-12<cosine<1-1e-12:return None
    guide=Acis.createBSplinesCurve(curve.spline,'forward',curve.subtype).Curve
    samples=[guide.value(guide.FirstParameter+(guide.LastParameter-guide.FirstParameter)*i/32) for i in range(33)]
    parameters=[lo+2*math.pi*(p-h.posCenter).dot(axis)/pitch for p in samples]
    steps=[b-a for a,b in zip(parameters,parameters[1:])]
    if not (all(d>0 for d in steps) or all(d<0 for d in steps)):return None
    matches=[];budget=max(1e-6,float(getattr(curve,'tolerance',0)))
    for delta in (math.acos(cosine),-math.acos(cosine)):
        major=(h.dirMajor*math.cos(delta)+h.dirMinor*math.sin(delta))*(cr/radius)
        minor=(h.dirMinor*math.cos(delta)-h.dirMajor*math.sin(delta))*(cr/radius)
        def point(u):return h.posCenter+major*math.cos(u)+minor*math.sin(u)+h.dirPitch*((u-lo)/(2*math.pi))
        if max((point(u)-p).Length for u,p in zip(parameters,samples))<=budget:
            matches.append((major,minor))
    if len(matches)!=1:return None
    major,minor=matches[0]
    lower,upper=min(parameters),max(parameters)
    margin=max(1e-5,(upper-lower)*0.01);lower-=margin;upper+=margin
    exact=Acis.Helix();exact.dirMajor=major;exact.dirMinor=minor;exact.dirPitch=h.dirPitch
    exact.posCenter=h.posCenter+h.dirPitch*((lower-lo)/(2*math.pi))
    exact.radAngles=Acis.Interval(Acis.Range('F',lower),Acis.Range('F',upper))
    bsc=exact.build().Curve
    # Independent analytic checks: points must lie on the cylinder and the
    # moving circular section, not merely near the stored approximation.
    for i in range(65):
        u=lower+(upper-lower)*i/64;p=bsc.value(u)
        moving=h.posCenter+h.dirMajor*math.cos(u)+h.dirMinor*math.sin(u)+h.dirPitch*((u-lo)/(2*math.pi))
        radial=(p-cylinder.center).cross(axis).Length
        if max(abs(radial-cr),abs((p-moving).Length-pr),abs((p-moving).dot(axis)))>1e-7:
            raise ValueError('Screw intersection does not lie on both analytic surfaces')
    if (parameters[-1]<parameters[0]) ^ (curve.sense=='reversed'):bsc.reverse()
    return splineData(bsc)


def intersectionSpline(curve):
    """Return a checked, oriented curve for supported analytic intersections.

    The stored intcurve is a guide, not the intersection geometry. Its millimetre
    error can be larger than the BRep tolerance. Use it only to identify the
    branch and direction; construct the geometry from both source surfaces.
    """
    if curve.subtype == 'ref':
        original = getattr(curve, 'curve', None)
        return intersectionSpline(original) if isinstance(original, Acis.CurveInt) else None
    if curve.subtype != 'int_int_cur' or curve.spline is None:
        return None
    sources = [getattr(curve, name, None) for name in ('surface1', 'surface2')]
    if hasattr(curve,'_exact_intersection'):return curve._exact_intersection
    screw=screwCylinderIntersection(curve,sources)
    if screw is not None:
        curve._exact_intersection=screw
        return screw
    if not all(isinstance(s, Acis.SurfaceCone) for s in sources):
        return None
    if any(abs(s.ratio-1)>1e-12 for s in sources):
        return None
    surfaces = [s.build().Surface for s in sources]
    guide = Acis.createBSplinesCurve(curve.spline, 'forward', curve.subtype).Curve
    lo, hi = guide.FirstParameter, guide.LastParameter
    samples = [guide.value(lo + (hi-lo)*i/16) for i in range(17)]
    budget = max(1e-6, float(getattr(curve, 'tolerance', 0)))
    matches = []
    for candidate in surfaces[0].intersect(surfaces[1]):
        if isinstance(candidate, Part.ArcOfEllipse):
            candidate = candidate.Ellipse
        if not isinstance(candidate, (Part.Hyperbola, Part.Ellipse, Part.BSplineCurve)):
            continue
        if isinstance(candidate, Part.BSplineCurve) and candidate.isClosed() and not candidate.isPeriodic():
            candidate.setPeriodic()
        parameters = [candidate.parameter(p) for p in samples]
        if candidate.isPeriodic():
            period = candidate.period()
            for i in range(1,len(parameters)):
                parameters[i] += round((parameters[i-1]-parameters[i])/period)*period
        deviation = max((candidate.value(u)-p).Length for u,p in zip(parameters,samples))
        steps = [b-a for a,b in zip(parameters,parameters[1:])]
        if deviation <= budget and (all(d>0 for d in steps) or all(d<0 for d in steps)):
            matches.append((candidate, parameters))
    if len(matches) != 1:
        return None
    candidate, parameters = matches[0]
    for u in parameters:
        p = candidate.value(u)
        if not all((s.value(*s.parameter(p))-p).Length <= 1e-6 for s in surfaces):
            raise ValueError('Cone intersection does not lie on both surfaces')
    lower, upper = min(parameters), max(parameters)
    margin = max(1e-3, (upper-lower)*0.05)
    reverse = (parameters[-1] < parameters[0]) ^ (curve.sense == 'reversed')
    if isinstance(candidate, Part.Ellipse):
        # A periodic STEP ellipse uses EDGE_CURVE.same_sense to choose its arc.
        # Unlike bounded guide splines, it must include ACIS's intcurve reversal.
        result = Acis.CurveEllipse()
        result.center = candidate.Center
        result.axis = -candidate.Axis if reverse else candidate.Axis
        result.major = candidate.XAxis*candidate.MajorRadius
        result.ratio = candidate.MinorRadius/candidate.MajorRadius
        curve._exact_intersection = result
        return result
    if isinstance(candidate, Part.BSplineCurve) and not candidate.isPeriodic():
        lower = max(candidate.FirstParameter, lower-margin)
        upper = min(candidate.LastParameter, upper+margin)
    else:
        lower -= margin
        upper += margin
    if isinstance(candidate, Part.BSplineCurve) and candidate.isPeriodic():
        bsc = candidate.copy()
    else:
        bsc = candidate.toBSpline(lower, upper)
    if reverse:
        bsc.reverse()
    # Check the analytic result independently against each surface before STEP.
    for i in range(17):
        p = bsc.value(bsc.FirstParameter+(bsc.LastParameter-bsc.FirstParameter)*i/16)
        if not all((s.value(*s.parameter(p))-p).Length <= 1e-6 for s in surfaces):
            raise ValueError('Analytic cone intersection does not lie on both surfaces')
    result = splineData(bsc)
    curve._exact_intersection = result
    return result
