"""
Genera el plano a escala de la tabla de la maqueta (hardware/maqueta/plano_tabla_maqueta.svg; 1 unidad = 1 mm).
Uso (desde la carpeta tesis): python scripts/generar_plano_tabla.py   -> escribe el SVG en la carpeta actual.
El PDF/PNG se exportaron desde el SVG con un navegador (Chromium).
"""
# Plano a escala de la tabla de la maqueta: 1 unidad SVG = 1 mm.
W,H=1100,800; M=60  # margen alrededor para cotas
def r(x,y,w,h,**k): return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '+' '.join(f'{a.replace("_","-")}="{b}"' for a,b in k.items())+'/>'
def l(x1,y1,x2,y2,**k): return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '+' '.join(f'{a.replace("_","-")}="{b}"' for a,b in k.items())+'/>'
def t(x,y,s,size=16,anchor="middle",color="#111",w="normal"): return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}" font-family="Arial" font-weight="{w}">{s}</text>'
o=[]
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-M-40} {-M-70} {W+2*M+520} {H+2*M+120}" width="{(W+2*M+420)}" height="{H+2*M+120}">')
o.append(r(-M-40,-M-70,W+2*M+420,H+2*M+120,fill="white"))
o.append(t(W/2,-M-35,"Plano de la tabla de la maqueta — escala 1:10 (medidas en mm)",24,w="bold"))
# tabla
o.append(r(0,0,W,H,fill="#e9e4d8",stroke="#000",stroke_width=3))
# calles
o.append(r(0,280,W,240,fill="#5a5a5a")); o.append(r(430,0,240,H,fill="#5a5a5a"))
# lineas de carril (blancas discontinuas) y central (amarilla doble)
for y in (340,460): o.append(l(0,y,430,y,stroke="white",stroke_width=3,stroke_dasharray="25,20")); o.append(l(670,y,W,y,stroke="white",stroke_width=3,stroke_dasharray="25,20"))
for x in (490,610): o.append(l(x,0,x,280,stroke="white",stroke_width=3,stroke_dasharray="25,20")); o.append(l(x,520,x,H,stroke="white",stroke_width=3,stroke_dasharray="25,20"))
for d in (-4,4):
    o.append(l(0,400+d,430,400+d,stroke="#f2c200",stroke_width=3)); o.append(l(670,400+d,W,400+d,stroke="#f2c200",stroke_width=3))
    o.append(l(550+d,0,550+d,280,stroke="#f2c200",stroke_width=3)); o.append(l(550+d,520,550+d,H,stroke="#f2c200",stroke_width=3))
# lineas de pare (20 mm antes del cruce, solo carriles que llegan)
o.append(l(690,280,690,400,stroke="white",stroke_width=8)); o.append(l(410,400,410,520,stroke="white",stroke_width=8))
o.append(l(430,260,550,260,stroke="white",stroke_width=8)); o.append(l(550,540,670,540,stroke="white",stroke_width=8))
# zonas de conteo (lineas punteadas de color, NO se pintan)
zonas={"norte":(690,280,370,120,"#1f77b4"),"sur":(40,400,370,120,"#ff9f00"),"este":(430,60,120,200,"#2ca02c"),"oeste":(550,540,120,200,"#d62ad6")}
for n,(x,y,w,h,c) in zonas.items(): o.append(r(x,y,w,h,fill=c,fill_opacity="0.18",stroke=c,stroke_width=3,stroke_dasharray="10,6"))
# flechas de sentido
def flecha(x,y,dx,dy):
    import math
    L=40; ex,ey=x+dx*L,y+dy*L; px,py=-dy,dx
    return f'<polygon points="{ex},{ey} {ex-dx*14+px*9},{ey-dy*14+py*9} {ex-dx*14-px*9},{ey-dy*14-py*9}" fill="white"/>'+l(x,y,ex-dx*10,ey-dy*10,stroke="white",stroke_width=4)
for y in (310,370): o.append(flecha(1000,y,-1,0)); o.append(flecha(120,y,-1,0))
for y in (430,490): o.append(flecha(80,y,1,0)); o.append(flecha(960,y,1,0))
for x in (460,520): o.append(flecha(x,110,0,1)); o.append(flecha(x,640,0,1))
for x in (580,640): o.append(flecha(x,700,0,-1)); o.append(flecha(x,150,0,-1))
# area que ve la camara a 1 m (medida)
o.append(r(40,60,1020,680,fill="none",stroke="#c00000",stroke_width=3,stroke_dasharray="18,8"))
# semaforos
sem={"S2":(705,255,"Cra 23 norte"),"S4":(405,255,"Dg 15 este"),"S1":(405,545,"Cra 23 sur"),"S3":(695,545,"Dg 15 oeste")}
for n,(x,y,_) in sem.items():
    o.append(r(x-14,y-14,28,28,fill="#111",rx=4)); o.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#3c3"/>')
    o.append(f'<circle cx="{x+22}" cy="{y}" r="5" fill="none" stroke="#000" stroke_width="2"/>')
    o.append(t(x,y-22 if y<400 else y+38,n,18,w="bold"))
# camara y poste
o.append(f'<circle cx="550" cy="400" r="18" fill="none" stroke="#c00000" stroke-width="3"/>'+l(535,385,565,415,stroke="#c00000",stroke_width=3)+l(565,385,535,415,stroke="#c00000",stroke_width=3))
o.append(r(835,765,30,30,fill="#7a4a1a")); o.append(l(850,765,563,413,stroke="#7a4a1a",stroke_width=6,stroke_dasharray="4,6")); o.append(t(850,758,"poste",14,color="#7a4a1a",w="bold"))
# ESP32 (debajo de la tabla)
o.append(r(900,680,110,60,fill="none",stroke="#004a99",stroke_width=3,stroke_dasharray="8,5")); o.append(t(955,715,"ESP32",16,color="#004a99",w="bold"))
# cotas
def cota_h(x1,x2,y,s): return l(x1,y,x2,y,stroke="#000",stroke_width=1.5)+l(x1,y-8,x1,y+8,stroke="#000")+l(x2,y-8,x2,y+8,stroke="#000")+t((x1+x2)/2,y-6,s,15)
def cota_v(x,y1,y2,s): return l(x,y1,x,y2,stroke="#000",stroke_width=1.5)+l(x-8,y1,x+8,y1,stroke="#000")+l(x-8,y2,x+8,y2,stroke="#000")+f'<text x="{x-8}" y="{(y1+y2)/2}" font-size="15" font-family="Arial" text-anchor="middle" transform="rotate(-90 {x-8} {(y1+y2)/2})">{s}</text>'
o.append(cota_h(0,W,-20,"1100")); o.append(cota_h(430,670,-45,"240 (Dg 15)")); o.append(cota_h(40,1060,H+30,"1020 vista de la cámara a 1 m"))
o.append(cota_v(-20,0,H,"800")); o.append(cota_v(-45,280,520,"240 (Cra 23)")); o.append(cota_v(W+25,60,740,"680 vista"))
o.append(cota_h(690,1060,262,"370 zona")); o.append(cota_v(420,60,260,"200 zona"))
# leyenda / notas
x0=W+70; y=10
items=[("rect","#5a5a5a","Calzada: pintura gris oscuro MATE"),("line","white","Carril 60 mm (4 por calle), discontinua blanca"),("line","#f2c200","Línea central doble amarilla"),
       ("line","white","Línea de pare: 20 mm antes del cruce"),("dash","#c00000","Lo que ve la cámara a 1 m (102 × 68 cm medido)"),
       ("zona","#1f77b4","Zonas de conteo por brazo (solo software, NO se pintan)"),("sem","#111","Semáforo (módulo LED) + hueco Ø8 mm para cables"),
       ("esp","#004a99","ESP32 + protoboard DEBAJO de la tabla"),("poste","#7a4a1a","Poste de la cámara en la acera (borde inferior, fuera de la vista);"),("txt","","   brazo en diagonal hasta el centro, lente a 1 m sobre la tabla")]
o.append(t(x0,y,"Convenciones",20,anchor="start",w="bold")); y+=30
for k,c,s in items:
    if k=="rect": o.append(r(x0,y-14,40,18,fill=c))
    elif k in("line",): o.append(r(x0,y-14,40,18,fill="#5a5a5a")); o.append(l(x0+4,y-5,x0+36,y-5,stroke=c,stroke_width=4))
    elif k=="dash": o.append(r(x0,y-14,40,18,fill="none",stroke=c,stroke_width=3,stroke_dasharray="8,4"))
    elif k=="zona": o.append(r(x0,y-14,40,18,fill=c,fill_opacity="0.25",stroke=c,stroke_dasharray="6,4"))
    elif k=="sem": o.append(r(x0+10,y-14,18,18,fill=c,rx=3))
    elif k=="esp": o.append(r(x0,y-14,40,18,fill="none",stroke=c,stroke_dasharray="6,4",stroke_width=2))
    elif k=="poste": o.append(r(x0+10,y-14,18,18,fill=c))
    elif k=="txt": pass
    o.append(t(x0+52,y,s,14,anchor="start")); y+=30
y+=10; o.append(t(x0,y,"Semáforos (hardware/esp32/conexiones.md)",18,anchor="start",w="bold")); y+=26
for s in ["S1 Cra 23 sur: D32 / D33 / D25","S2 Cra 23 norte: D26 / D27 / D13","S3 Dg 15 oeste: D23 / D22 / D21","S4 Dg 15 este: D19 / D18 / D17"]:
    o.append(t(x0,y,s,14,anchor="start")); y+=22
y+=12; o.append(t(x0,y,"Notas",18,anchor="start",w="bold")); y+=26
for s in ["Tránsito por la derecha (Colombia).","2 carriles de llegada por brazo, como la red SUMO.","Capacidad estimada por brazo: Cra 23 ≈ 8 carros,",
          "   Dg 15 ≈ 4 (Hot Wheels de 7 cm + 1,5 cm).","SIN texto ni dibujos en la tabla (falsos positivos).","Acabado mate (sin barniz brillante).",
          "Semáforos en las aceras, fuera de las zonas.","Poste: 60 mm de margen inferior, fuera de la vista.","Las calles llegan al borde: los carros entran","   desde fuera de la vista."]:
    o.append(t(x0,y,s,14,anchor="start")); y+=21
o.append('</svg>')
open('plano_tabla_maqueta.svg','w').write('\n'.join(o))
