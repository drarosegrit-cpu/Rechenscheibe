def AddNumbers(text,re,ho,height,angle,alignment):
    t = modspc.add_text(text).set_pos((re,ho), align=alignment)
    t.dxf.style = "OpenSans-Italic"
    t.dxf.height = height
    t.dxf.layer = "Numbers"
    t.dxf.rotation = angle

def PlotLogScales(doc,radius):

    doc.layers.new(name="InnerRing")
    doc.layers.new(name="OuterRing")

    incList = [1, 2, 5]           # inkrement der log skala in 1/100stel
    threshold = 0.4               # grenzwert fuer den abstand der skalenstriche in mm
    x = 100                       # erste zahl auf der log skala (in 1/100stel)
    y = 0                         # Log10(1)=0
    dash = 0.5                    # strichlänge in mm
    circumfrnc = 2*radius*pi      # umfang der rechenscheibe
    hgtNum=3.0                    # Basis-Textgroesse

    arc = 0                       # bogenlaenge von log10(1)
    inc = incList.pop(0)          # hole das (wachsende) inkrement aus der liste

    # x-wert der log skala geht von 1 bis 10 (10=1000/100)
    while x < 1000:

        x += inc                  # basiswert hochzaehlen
        y = log10(x/100)          # log10(basiswert) geht von 0 bis 1
        angle = y*360             # und als winkel
        # abstand der skalenstriche - wird benoetigt um das x-inkrement zu berechnen
        deltaArc = y*circumfrnc-arc
        arc = y*circumfrnc        # aktuellen bogen merken

        f = 1                       # mach den strich bei runden zahlen laenger
        if(x % 10 == 0): f = 2
        if(x % 50 == 0): f = 3
        if(x % 100 == 0):f = 4

    #   winkel wird umgerechet von mathematisch (von ost aus linksdrehend) in seemaennisch (von nord aus rechtsdrehend)
        cs = cos(radians(90-angle))
        sn = sin(radians(90-angle))
        re0 = cs*radius
        ho0 = sn*radius
        re1 = cs*(radius-f*dash)
        ho1 = sn*(radius-f*dash)
        modspc.add_line((re0, ho0), (re1, ho1), dxfattribs={'layer': "InnerRing"})

        re3 = cs*(radius+f*dash)
        ho3 = sn*(radius+f*dash)
        modspc.add_line((re0, ho0), (re3, ho3), dxfattribs={'layer': "OuterRing"})

        n=x/100
        if(n==10): n=1
        if( f==3 and n<6): #text,re,ho,height,angle,alignment
            text="{:1.1f}".format(n)
            AddNumbers(text,re1,ho1,0.6*hgtNum,90-angle,"MIDDLE_RIGHT")
            AddNumbers(text,re3,ho3,0.6*hgtNum,90-angle,"MIDDLE_LEFT")
        if(f==4):
            text="{:1.0f}".format(n)
            AddNumbers(text,re1,ho1,hgtNum,90-angle,"MIDDLE_RIGHT")
            AddNumbers(text,re3,ho3,hgtNum,90-angle,"MIDDLE_LEFT")


                


        if(x % 100 == 0):
            #print("checking inc: ", x/100, inc, deltaArc)
            if(deltaArc < threshold):
                inc = incList.pop(0)
                #print("new inc: ", inc)
        #print("{} {:8.4f} {:8.4f} {:8.4f} {:8.4f} {:8.4f}".format(x, x/100, y, inc/100))
    print("Finished")

def PlotRays(dxfDoc,modelSpace,radius,awaRadius):

    lyAwaAngle="awaAngle"
    lyAwaSpeed="awaSpeed"

    rho=57.2958
    p0=Point2(0,0)                  # mittelpunkt der rechenscheibe
    p1=Point2(0,-awaRadius)          # awaRadius = radius der scheinbaren windgeschwindigkeit

    c1=Circle(p0,float(radius))      # kreis mit radius der rechenscheibe

    # r1: strahl vom mittelpunkt des awa-kreises rechtsdrehend inkrement 10 grad
    doc.layers.new(name=lyAwaAngle)
    for a in range(0,360,10):   
        r1=Ray2(p1,Vector2(sin(radians(90-a)),cos(radians(90-a)))) 
        # schneide strahl mit kreis rechenscheibe
        # i = LineSegment vom kreismittelpunkt bis kreis
        i=r1.intersect(c1)          
        modelSpace.add_line((i.p1.x,i.p1.y),(i.p2.x,i.p2.y),dxfattribs={"layer":lyAwaAngle})

    doc.layers.new(name=lyAwaSpeed)
    for i in range(0,30,2):
        c2Rad=i*awaRadius/10
        c2=Circle(p1,c2Rad)
        i=c1.intersect(c2)
        if(i is not None):
            lPoint=i[0]-p1
            a0=rho*atan2(lPoint.y,lPoint.x)
            rPoint=i[1]-p1
            a1=rho*atan2(rPoint.y,rPoint.x)

            modelSpace.add_arc((p1.x,p1.y), c2Rad, a1,a0,dxfattribs={"layer":lyAwaSpeed})

def PlotCompass(dxfDoc,modelSpace,radius,dRadius,dAngle,txtHgt,txtDst):

    # layer oeffnen compass
    dxfDoc.layers.new(name="Compass",dxfattribs={"color":7})
    # kreis zeichnen (0,0,radius)
    modelSpace.add_circle((0,0),radius,dxfattribs={"layer":"Compass"})
    # kreis zeichnen (0,0,radius-dRadius)
    modelSpace.add_circle((0,0),radius-dRadius,dxfattribs={"layer":"Compass"})
    # gradstriche zeichnen abstand dAngle
    for a in range(0, 360, dAngle):
        cs=cos(radians(a))
        sn=sin(radians(a))
        re0=cs*radius
        ho0=sn*radius
        re1=cs*(radius-dRadius)
        ho1=sn*(radius-dRadius)
        modelSpace.add_line((re0,ho0),(re1,ho1),dxfattribs={"layer":"Compass"})
    # layer oeffen gradzahlen
    doc.layers.new(name="CompassNumbers",dxfattribs={"color":7})

    s="OpenSans-Italic"
    l="CompassNumbers"
    h=txtHgt
    mr="MIDDLE_RIGHT"
    ml="MIDDLE_LEFT"
    al=mr
    if(dRadius<0): al=ml
    a=180
    for angle in range(-90,90,30):
        t="{:02.0f}".format(a/10)
        re0=cos(radians(angle))*(radius-dRadius*txtDst)
        ho0=sin(radians(angle))*(radius-dRadius*txtDst)
        modelSpace.add_text(t,dxfattribs={"rotation":angle,"height":h,"style":s,"layer":l}).set_pos((re0,ho0),align=al)
        a-=30
        
    al=ml
    if(dRadius<0): al=mr
    a=360
    for angle in range(90,270,30):
        t="{:02.0f}".format((a/10)%360)
        re0=cos(radians(angle))*(radius-dRadius*txtDst)
        ho0=sin(radians(angle))*(radius-dRadius*txtDst)
        modelSpace.add_text(t,dxfattribs={"rotation":angle+180,"height":h,"style":s,"layer":l}).set_pos((re0,ho0),align=al)
        a-=30
    # gradzahlen zeichnen

def PlotPolarSpeed(dxfDoc,modelSpace,speedTableFile,radius):

    lyPolar="polarSpd"
    dxfDoc.layers.new(name=lyPolar)

    try:
        speedTable=xls.load_workbook(speedTableFile)
    except IOError as e:
        print(speedTableFile)
        print("{0} Kann Datei nicht oeffnen".format(e))
        sys.exit()
    
    polarSpeedSheet=speedTable["Values"]
    value=polarSpeedSheet["a1"].value
    print(value)

    # a2-a74 = winkel
    # b-h = knts (6,8,10,12,14,16,20) = 7 Werte
    polarSpeed =polarSpeedSheet["a2":"h74"]
    
    xylist=[ [],[],[],[],[],[],[] ]
    for row in polarSpeed:
        pa=radians(90-row[0].value)
        j=0
        for i in range(1,8,1):
            knt=row[i].value
            re=cos(pa)*knt*radius
            ho=sin(pa)*knt*radius
            xylist[j].append((re,ho))
            j+=1
    i=0
    for r in xylist:
        modelSpace.add_lwpolyline(r,dxfattribs={"layer":lyPolar})


############################################################################################
# main begins here
import ezdxf
from math import sin, cos, pi, radians, log10, atan2
from euclid import Point2, Circle, Ray2, Vector2
import openpyxl as xls
import sys
from os.path import expanduser



doc = ezdxf.new('R2010')
modspc = doc.modelspace()

radius=50
logRadius=15+radius
dRadius=-5
dAngle=10
#rWS=1.3             # ratio geschwindgkeit wind zu schiff
rWS=1.0
awaRadius=radius/rWS

txtHgt=3.8
txtDst=1.2

#speedTableFile=expanduser('~')+"/Dokumente/PythonProjects/Rechenscheibe/J125.xlsx"
speedTableFile="K:/.shortcut-targets-by-id/0B3bQ1ojUsF0Ka2ZJcllUMGZBaEE/Segeln/PythonProjects/Rechenscheibe"+"/J125.xlsx"
print(speedTableFile)
PlotPolarSpeed(doc,modspc,speedTableFile,awaRadius)
PlotLogScales(doc,logRadius)
PlotCompass(doc,modspc,radius,dRadius,dAngle,txtHgt,txtDst)
PlotRays(doc,modspc,radius,awaRadius)

doc.saveas('test.dxf')