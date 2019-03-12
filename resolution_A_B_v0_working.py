# -*- coding: utf-8 -*-
"""
Reads gcode and calculates the nozzle and extruder positioning
"""
import math

def read_gcode(gcode_name,relative_E,str_limits):
    
    gcode_list = list()
    
    first_line = [0.0,0.0,0.0,0.0]
    
    gcode_list.append(first_line)
    
    gcode_file = open(gcode_name,'r')
    
    cont_line = 0
    
    str_init = str_limits[0] + '\n'
    str_end = str_limits[1] +'\n'#str_end must be the string just after the the CDP has been finished
    
    flag_init = 0
    
    index_init = -1
    index_end = -1
    
    for line in gcode_file:
        
        if line == str_init and flag_init == 0:
            flag_init = 1
            index_init = cont_line + 1
            
        if line == str_end and flag_init == 1:
            index_end = cont_line
            
        aux_line = line.split()
        
        if aux_line[0] == 'G1':
            
            last_line = gcode_list[cont_line]
            x0 = last_line[0]
            y0 = last_line[1]
            z0 = last_line[2]
            e0 = last_line[3]
            
            cont_line = cont_line + 1
            
            flag_E = 0
            
            for i in range(1,len(aux_line)):
                
                elem_line = aux_line[i]
                
                if elem_line[0] == 'X':
                    coord = float(elem_line[1::])

                    x0 = coord
                                      
                elif elem_line[0] == 'Y':
                    coord = float(elem_line[1::])
                    
                    y0 = coord
                    
                elif elem_line[0] == 'Z':
                    coord = float(elem_line[1::])
                    
                    z0 = coord
                    
                elif elem_line[0] == 'E':
                    coord = float(elem_line[1::])
                    
                    e0 = coord
                    
                    flag_E = 1

            #It extrusion is relative, but there is not a command to extrude, the actual value of extrusion must be 0
            if relative_E == 1 and flag_E == 0:
                e0 = 0.0
                
            gcode_list.append([x0,y0,z0,e0])   

    
    gcode_file.close()
    
    return gcode_list, index_init, index_end
#------------------------------------------------------------------------------
def A_B_calculate(dX,dY):
    dA = dX + dY
    dB = dX - dY
    return dA, dB
#------------------------------------------------------------------------------
def X_Y_calculate(dA,dB):
    dX = (dA + dB)*0.5
    dY = (dA - dB)*0.5
    return dX, dY
#------------------------------------------------------------------------------
    
#gcode_name = 'teste96_4.gcode'
#gcode_name = 'CDP_1LAYER.gcode'
gcode_name = 'ED_V16_0325_RE_2.gcode'

volco_name = 'Toolpath_22fil_V16_A_B_L50_teste.csv'

str_limits = ['G1 X182.429000 Y96.548000 F12000.000','G1 E-6.0000 F3600']

relative_E = 1 # 1 = relative extrusion

Nfil = 22 #number of filaments per layer

#List of movements
gcode_list, index_init, index_end = read_gcode(gcode_name,relative_E,str_limits)

print 'Coupon initial index = %d' %index_init
print 'Coupon final index = %d' %index_end

Ar = 80.0 # steps/mm
Br = 80.0 # steps/mm
Zr = 400.0 # steps/mm
Er = 374.4 # steps/mm

#Counting steps
count_steps = [0, 0, 0, 0] #[X,Y,Z,E] axis

initial_coordinates = [0., 0., 0., 0.] #[X,Y,Z,E] axis

#Real coordinates influenced by the resolution of the motors
actual_coordinates = list() #[X,Y,Z,E] axis
actual_coordinates.append([0., 0., 0., 0.])

#Number of steps required to print the current filament. 
current_n_steps = list()
current_n_steps.append([0, 0])

#List created to check if the results are correct
checking_coordinates = list()
checking_coordinates.append([0., 0.])

initial_coordinates_check = [0., 0.,] #[X,Y] axis

for i in range(1,len(gcode_list)):
    
    line_i = gcode_list[i]
    
    dX = line_i[0]
    dY = line_i[1]
    dZ = line_i[2]
    dE = line_i[3]
    
    #number of steps to achieve the desired position from the origin
#    na = round(dX*Ar)
#    nb = round(dY*Br)
#    nz = round(dZ*Zr)
#    ne = round(dE*Er)
    
    na = math.floor(dX*Ar + 0.5)
    nb = math.floor(dY*Br + 0.5)
    nz = math.floor(dZ*Zr + 0.5)
    ne = math.floor(dE*Er + 0.5)
    
    #number of steps required from the current position to the desired position
    na_s = na - count_steps[0]
    nb_s = nb - count_steps[1]
    nz_s = nz - count_steps[2]
    
    if relative_E == 1:
        ne_s = ne
    else:
        ne_s = ne - count_steps[3]
        
    #updating total number of steps
    count_steps[0] = na
    count_steps[1] = nb
    count_steps[2] = nz
    count_steps[3] = ne
    
    #Calculating actual position of the axis
    dA = (na_s + nb_s)/Ar
    dB = (na_s - nb_s)/Br
    dX, dY = X_Y_calculate(dA,dB)
    
    dZ_actual = nz_s / Zr
    dE_actual = ne_s / Er
    
    initial_coordinates[0] = initial_coordinates[0] + dX
    initial_coordinates[1] = initial_coordinates[1] + dY
    initial_coordinates[2] = initial_coordinates[2] + dZ_actual
    initial_coordinates[3] = initial_coordinates[3] + dE_actual
    
    Xi = initial_coordinates[0]
    Yi = initial_coordinates[1]
    Zi = initial_coordinates[2]
    Ei = initial_coordinates[3]
    
    if relative_E == 1:
        Ei = dE_actual
        
    aux_coord = [Xi, Yi, Zi, Ei]
    actual_coordinates.append(aux_coord)
    
    #Current number of steps to print the current filament for A and B axis
    na = na_s + nb_s
    nb = na_s - nb_s
    current_n_steps.append([na, nb])
    
    #Displacements deltaA and deltaB
    dA = na/Ar
    dB = nb/Br
    dX, dY = X_Y_calculate(dA,dB) #Displacements deltaX and deltaY provoked by moviments of A and B axis.
    
    initial_coordinates_check[0] = initial_coordinates_check[0] + dX
    initial_coordinates_check[1] = initial_coordinates_check[1] + dY
    
    Xnew = initial_coordinates_check[0]
    Ynew = initial_coordinates_check[1]
    
    checking_coordinates.append([Xnew, Ynew])

#Calculating displacement list. It is the difference between the old and current coordinates.    
dist_list = list()

for i in range(1,len(actual_coordinates)):
    
    old_coord = actual_coordinates[i-1]
    new_coord = actual_coordinates[i]
    
    dx = new_coord[0] - old_coord[0]
    dy = new_coord[1] - old_coord[1]
    dz = new_coord[2] - old_coord[2]
    de = new_coord[3] - old_coord[3]
    
    dist_list.append([dx,dy,dz,de])
    
#Generating list to be inserted in VOLCO
init_coord = actual_coordinates[index_init]
x0 = init_coord[0]; y0 = init_coord[1]; z0 = init_coord[2]

coord_volco = list()

# First coordinate to be inserted in VOLCO list:
coord_now = actual_coordinates[index_init]
    
xi = coord_now[0]
yi = coord_now[1]
zi = coord_now[2]

xnew = abs(xi - x0)
ynew = abs(yi - y0)

aux_list = [xnew,ynew,zi]
coord_volco.append(aux_list)
      
for i in range(index_init+1,index_end + 1):
    
    coord_now = actual_coordinates[i]
    
    xi = coord_now[0]
    yi = coord_now[1]
    zi = coord_now[2]
    
    xnew = abs(xi - x0)
    ynew = abs(yi - y0)
    
    aux_list = [xnew,ynew,zi]
    
    if xnew == coord_volco[-1][0] and ynew == coord_volco[-1][1]: #this means that the nozzle move only in the z direction
        print 'z displacement'
        del coord_volco[-1] #because the last line in each layer it not correct, since it contains the small filament
    else:
        coord_volco.append(aux_list)


del coord_volco[-1] #because the last line in the last layer it not correct, since it contains the small filament

#Writing the gcode in the format VOLCO can read

file_volco = open(volco_name,'w')
for i in range(0,len(coord_volco),2):
    
    coord_0 = coord_volco[i]
    e0 = 0
    
    coord_1 = coord_volco[i+1]
    e1 = 1
    
    str_write = '%f, %8.8f, %f, %d\n' %(0.0,coord_0[1]/1000,coord_0[2]/1000,e0)
#    str_write = '%f, %8.8f, %f, %d\n' %(coord_0[0]/1000,coord_0[1]/1000,coord_0[2]/1000,e0)
    file_volco.write(str_write)
    
    str_write = '%f, %8.8f, %f, %d\n' %(0.005,coord_1[1]/1000,coord_1[2]/1000,e1)
#    str_write = '%f, %8.8f, %f, %d\n' %(coord_1[0]/1000,coord_1[1]/1000,coord_1[2]/1000,e1)
    file_volco.write(str_write)
    
file_volco.close()

#Testing VOLCO file
file_volco = open(volco_name,'r')

volco_test = list()

cont = -1
for line in file_volco:
    
    line = line.split(',')
    x = float(line[0])
    y = float(line[1])
    z = float(line[2])
    
    cont = cont + 1
    
    if cont % (2*Nfil) == 0:
        y0 = float(line[1])
        aux_list = [float(x),float(y0),float(z)]
        print cont
    else:
        y = float(line[1])
        aux_list = [float(x),float(y)-y0,float(z)]
        
        y0 = y
        
    volco_test.append(aux_list)
    
file_volco.close()
    
    


    
    
