"""Esquema de TRAZADO de la tabla (todas las medidas), version con puente. 1 unidad = 1 mm. Origen: esquina sup. izq."""
W,H=1100,800
o=[]
def L(x1,y1,x2,y2,c="#000",w=2,d=None): return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"'+(f' stroke-dasharray="{d}"' if d else '')+'/>'
def T(x,y,s,sz=14,a="middle",c="#111",b="normal",rot=None):
    tr=f' transform="rotate({rot} {x} {y})"' if rot is not None else ''
    return f'<text x="{x}" y="{y}" font-size="{sz}" text-anchor="{a}" fill="{c}" font-family="Arial" font-weight="{b}"{tr}>{s}</text>'
VB=(-230,-200,W+230+660,H+200+200)
o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{VB[0]} {VB[1]} {VB[2]} {VB[3]}" width="{VB[2]}" height="{VB[3]}">')
o.append(f'<rect x="{VB[0]}" y="{VB[1]}" width="{VB[2]}" height="{VB[3]}" fill="white"/>')
o.append(T(W/2,-160,"Esquema de trazado de la maqueta (tabla 1100 × 800 mm) — medidas en mm desde la esquina superior izquierda",22,b="bold"))
# tabla y calzada
o.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#EAE6CA" stroke="#000" stroke-width="3"/>')
o.append(f'<polygon points="0,280 842,280 882,340 {W},340 {W},460 882,460 842,520 0,520" fill="#8D948D"/>')
o.append(f'<rect x="430" y="0" width="240" height="{H}" fill="#8D948D"/>')
# bordes del puente
o.append(L(842,280,882,340,"#000",3)); o.append(L(882,340,W,340,"#000",3)); o.append(L(842,520,882,460,"#000",3)); o.append(L(882,460,W,460,"#000",3))
# central doble amarilla
for d in (-4,4):
    o.append(L(0,400+d,430,400+d,"#F7B500",3)); o.append(L(670,400+d,W,400+d,"#F7B500",3))
    o.append(L(550+d,0,550+d,280,"#F7B500",3)); o.append(L(550+d,520,550+d,H,"#F7B500",3))
# carriles discontinuos
for y in (340,460): o.append(L(0,y,430,y,"white",3,"25,20")); o.append(L(670,y,842,y,"white",3,"25,20"))
for x in (490,610): o.append(L(x,0,x,280,"white",3,"25,20")); o.append(L(x,520,x,H,"white",3,"25,20"))
# lineas de pare
o.append(L(690,280,690,400,"white",8)); o.append(L(410,400,410,520,"white",8)); o.append(L(430,260,550,260,"white",8)); o.append(L(550,540,670,540,"white",8))
# flechas de sentido (solo indicativas, NO se pintan)
def fl(x,y,dx,dy):
    ex,ey=x+dx*36,y+dy*36; px,py=-dy,dx
    return L(x,y,ex-dx*8,ey-dy*8,"#fff",3)+f'<polygon points="{ex},{ey} {ex-dx*12+px*7},{ey-dy*12+py*7} {ex-dx*12-px*7},{ey-dy*12-py*7}" fill="#fff"/>'
for y in (310,370): o.append(fl(250,y,-1,0)); o.append(fl(780,y,-1,0))
o.append(fl(1010,400-30,-1,0)); o.append(fl(980,430,1,0))
for y in (430,490): o.append(fl(200,y,1,0)); o.append(fl(740,y,1,0))
for x in (460,520): o.append(fl(x,120,0,1)); o.append(fl(x,640,0,1))
for x in (580,640): o.append(fl(x,700,0,-1)); o.append(fl(x,180,0,-1))
# semaforos y huecos
sem={"S1":(405,545,(405,545),"←"),"S2":(705,255,(705,255),"→"),"S3":(695,545,(695,545),"↓"),"S4":(405,255,(405,255),"↑")}
for n,(x,y,(hx,hy),dirr) in sem.items():
    o.append(f'<rect x="{x-12}" y="{y-12}" width="24" height="24" rx="4" fill="#111"/>')
    o.append(f'<circle cx="{hx}" cy="{hy}" r="4" fill="white" stroke="#c00" stroke-width="2"/>')  # hueco bajo el poste
    o.append(T(x+(-55 if x<550 else 55),y+(-32 if y<400 else 48),f"{n} ({x},{y})",13,b="bold"))
# poste y camara
o.append('<rect x="835" y="765" width="30" height="30" fill="#7a4a1a"/>'); o.append(T(850,758,"poste (850,780)",12,c="#7a4a1a",b="bold"))
o.append('<circle cx="550" cy="400" r="14" fill="none" stroke="#c00" stroke-width="3"/>'+L(540,390,560,410,"#c00",3)+L(560,390,540,410,"#c00",3))
o.append(T(550,438,"lente a 1000 mm sobre (550,400)",12,c="#c00",b="bold"))
# cadenas de cotas
def cadena_x(xs,y,tick=10):
    s=L(xs[0],y,xs[-1],y,"#000",1.2)
    for x in xs: s+=L(x,y-tick,x,y+tick,"#000",1.2)+T(x+(10 if x==690 else (-8 if x==670 else 0)),y-14+(30 if x==690 else 0),str(x),12,b="bold")
    return s
def cadena_y(ys,x,tick=10):
    s=L(x,ys[0],x,ys[-1],"#000",1.2)
    for y in ys: s+=L(x-tick,y,x+tick,y,"#000",1.2)+T(x-16,y+4,str(y),12,a="end",b="bold")
    return s
o.append(cadena_x([0,430,490,550,610,670,690,842,882,1100],-40))
o.append(T(W/2,-75,"Coordenadas X (mm) de bordes, líneas de carril, línea de pare norte e inicio/fin del estrechamiento del puente",13,c="#333"))
o.append(cadena_y([0,260,280,340,400,460,520,540,800],-40))
o.append(T(-150,400,"Coordenadas Y (mm)",13,c="#333",rot=-90))
# distancias utiles abajo
def cota(x1,x2,y,s): return L(x1,y,x2,y,"#000",1.2)+L(x1,y-8,x1,y+8,"#000",1.2)+L(x2,y-8,x2,y+8,"#000",1.2)+T((x1+x2)/2,y+18,s,12)
o.append(cota(430,670,H+35,"Dg 15: 240 (4 carriles × 60)")); o.append(cota(690,842,H+35,"152 (2 carriles, 41 m)"))
o.append(cota(842,882,H+75,"40 transición")); o.append(cota(882,1100,H+35,"218 puente (1 carril por sentido)"))
o.append(cota(0,430,H+35,"430"))
# tabla de referencia
x0=W+60; y=-110
def fila(txt,sz=14,b="normal",c="#111"):
    global y; o.append(T(x0,y,txt,sz,a="start",b=b,c=c)); y+=sz+8
fila("Referencia de trazado",20,"bold"); y+=4
fila("CALZADA",15,"bold")
fila("Cra 23 (horizontal): y = 280 a 520, de x = 0 a 1100")
fila("   excepto puente: desde x = 882, solo y = 340 a 460")
fila("   transición 842→882: diagonal (842,280)–(882,340)")
fila("   y (842,520)–(882,460)")
fila("Dg 15 (vertical): x = 430 a 670, de y = 0 a 800")
y+=6; fila("CARRILES: 60 mm (4 por calle; puente 2)",15,"bold")
fila("Cra 23: blanca discontinua en y = 340 y y = 460")
fila("   de x = 0 a 430 y de x = 670 a 842 (no en el puente)")
fila("Dg 15: blanca discontinua en x = 490 y x = 610")
fila("   de y = 0 a 280 y de y = 520 a 800")
fila("Discontinua: 25 mm de línea + 20 mm de espacio")
y+=6; fila("LÍNEA CENTRAL doble amarilla continua",15,"bold")
fila("Cra 23: y = 396 y y = 404 (x 0–430 y 670–1100)")
fila("Dg 15: x = 546 y x = 554 (y 0–280 y 520–800)")
fila("No se pinta nada dentro del cruce (430–670 × 280–520)")
y+=6; fila("LÍNEAS DE PARE: blancas, 8 mm de ancho",15,"bold")
fila("Norte (Cra 23, derecha): x = 690, de y = 280 a 400")
fila("Sur (Cra 23, izquierda): x = 410, de y = 400 a 520")
fila("Este (Dg 15, arriba): y = 260, de x = 430 a 550")
fila("Oeste (Dg 15, abajo): y = 540, de x = 550 a 670")
y+=6; fila("SEMÁFOROS: poste hueco de ~80 mm sobre hueco Ø8",15,"bold")
fila("(centro del poste = centro del hueco; LED de frente al carril)")
fila("S1 Cra 23 sur: (405,545) · LED miran a la izquierda")
fila("S2 Cra 23 norte: (705,255) · LED miran a la derecha")
fila("S3 Dg 15 oeste: (695,545) · LED miran hacia abajo")
fila("S4 Dg 15 este: (405,255) · LED miran hacia arriba")
fila("Cables por dentro del poste hasta el ESP32 (debajo)")
y+=6; fila("CÁMARA",15,"bold")
fila("Poste en (850,780); lente a 1000 mm sobre (550,400)")
fila("Imagen horizontal, lado largo paralelo a la Cra 23")
y+=6; fila("COLORES (todo MATE; RAL = referencia, sirve equivalente)",15,"bold")
fila("Calzada: gris medio tipo asfalto, RAL 7042 (gris tráfico A)")
fila("   NO gris muy oscuro: los carros negros/azules se pierden")
fila("Aceras y resto de la tabla: hueso/beige claro, RAL 1013")
fila("Carriles, pare: blanco, RAL 9016 (blanco tráfico)")
fila("Línea central: amarillo, RAL 1023 (amarillo tráfico)")
fila("Postes de semáforo: negro mate, RAL 9005")
fila("Bordes del puente: línea negra o gris oscuro, 3–5 mm")
y+=6; fila("NOTAS",15,"bold")
fila("Las flechas blancas del dibujo NO se pintan.")
fila("Sin texto ni dibujos sobre la tabla. Sin barniz brillante.")
fila("Tránsito por la derecha. Medir siempre desde la")
fila("esquina superior izquierda (lado de 1100 arriba).")
o.append('</svg>')
open('esquema_trazado_maqueta.svg','w').write('\n'.join(o))
