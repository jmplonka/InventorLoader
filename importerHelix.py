"""Accurate screw-sweep surfaces from the analytic ACIS sweep recipe."""
import math
import FreeCAD as App
import Part


def sweepSurface(surface):
    profile=getattr(surface,'profile',None)
    path=getattr(surface,'path',None)
    helix=getattr(path,'helix',None)
    if helix is None or profile is None or getattr(profile,'__name__','')!='ellipse':
        return None
    if abs(helix.facApex)>1e-12 or abs(profile.ratio-1)>1e-12:
        return None
    lo=helix.radAngles.getLowerLimit();hi=helix.radAngles.getUpperLimit()
    if hi<=lo:
        raise ValueError('Invalid sweep interval')
    axis=helix.dirMajor.cross(helix.dirMinor)
    axis.normalize()
    expected=helix.posCenter+helix.dirMajor*math.cos(lo)+helix.dirMinor*math.sin(lo)
    if (expected-profile.center).Length>1e-6:
        return None
    if abs(abs(profile.axis.normalize().dot(axis))-1)>1e-9:
        return None
    # Reconstruct from the circular profile and screw motion; stored display
    # splines can deviate by 0.01 mm.
    circle=Part.Circle(profile.center,profile.axis,profile.major.Length)
    # C2 periodic interpolation avoids the C0 knot joins of the usual rational
    # circle representation, which cause OpenCascade's Boolean checker to reject
    # an otherwise smooth swept surface.
    section=Part.BSplineCurve()
    count=128
    angles=[2*math.pi*i/count for i in range(count+1)]
    section.interpolate(Points=[circle.value(u) for u in angles[:-1]],Parameters=angles,PeriodicFlag=True,Tolerance=1e-10)
    section.setNotPeriodic()
    def moved(p,v):
        rotation=App.Rotation(axis,math.degrees(v-lo))
        return helix.posCenter+rotation.multVec(p-helix.posCenter)+helix.dirPitch*((v-lo)/(2*math.pi))
    n=max(8,int(math.ceil((hi-lo)/(math.pi/32))))
    while n<=65536:
        params=[lo+(hi-lo)*i/n for i in range(n+1)]
        curves=[]
        for pole in section.getPoles():
            curve=Part.BSplineCurve()
            curve.interpolate(Points=[moved(pole,v) for v in params],Parameters=params,Tolerance=1e-9)
            curves.append(curve)
        first=curves[0]
        if any(c.getKnots()!=first.getKnots() or c.getMultiplicities()!=first.getMultiplicities() for c in curves):
            raise ValueError('Inconsistent sweep interpolation basis')
        bss=Part.BSplineSurface()
        bss.buildFromPolesMultsKnots(
            [c.getPoles() for c in curves],section.getMultiplicities(),first.getMultiplicities(),
            section.getKnots(),first.getKnots(),False,False,section.Degree,first.Degree,
            [[weight]*first.NbPoles for weight in section.getWeights()])
        error=0.0
        for i in range(n):
            v=(params[i]+params[i+1])/2
            for u in (0,0.7,1.8,3.1,4.2,5.5):
                error=max(error,(bss.value(u,v)-moved(section.value(u),v)).Length)
        if error<=1e-7:
            if getattr(surface,'spline',None) is None:
                return bss
            import Acis
            original=Acis.createBSplinesSurface(surface.spline).Surface
            u0=(original.getUKnots()[0]+original.getUKnots()[-1])/2
            v0=(original.getVKnots()[0]+original.getVKnots()[-1])/2
            p=original.value(u0,v0)
            u1,v1=bss.parameter(p)
            if original.normal(u0,v0).dot(bss.normal(u1,v1))<0:
                bss.exchangeUV()
            return bss
        n*=2
    raise ValueError('Analytic ACIS sweep approximation did not converge')
