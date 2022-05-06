import math

from matplotlib import pyplot
import numpy
import os

# if true, plot
plot = True

# device and file specific parameters
vorlax_folder = r"C:\Users\kenet\ASU\F21 and Below\MAE564\VORLAX"
input_file = r"capstone_rc_original.inp"


# define wing design function
def wing_design():
    global angle_of_attack, twist
    global input_file, vorlax_folder
    global NPAN, NVOR, RNCV
    global mean_chord, wing_area
    global mach, gamma

    ainc1 = []
    ainc2 = []
    for i in range(len(twist) - 1):
        ainc1.append(twist[i])
        ainc2.append(twist[i + 1])

    temp_input_file = input_file[0:len(input_file) - 13] + ".inp"
    temp_file = open(vorlax_folder + "\\" + temp_input_file, 'w')
    for count, input_line in enumerate(input_data):
        # write in angle of attack
        if count == 8:
            input_line = "1.0       " + str(angle_of_attack) + "\n"
        if count in twist_index_upper:
            input_line = input_line.rsplit('+', 1)
            temp_line = input_line[1]
            input_line = str(ainc1[0]) + " " * (10 - len(str(ainc1[0])))
            input_line += str(ainc2[0]) + " " * (10 - len(str(ainc2[0])))
            input_line += '+' + temp_line
        elif count in twist_index_lower:
            temp_angle_upper = ainc1.pop(0)
            temp_angle_lower = ainc2.pop(0)
            input_line = input_line.rsplit('-', 1)
            temp_line = input_line[1]
            input_line = str(temp_angle_upper) + " " * (10 - len(str(temp_angle_upper)))
            input_line += str(temp_angle_lower) + " " * (10 - len(str(temp_angle_lower)))
            input_line += '-' + temp_line
        temp_file.write(input_line)
    temp_file.close()

    command = "cd " + vorlax_folder + " && vorlax2020.exe <" + temp_input_file + "> "
    command += temp_input_file[0:len(input_file) - 3] + ".csv"
    os.system(command)

    collect = False
    cn = []
    cl = []
    cp_upper = []
    cp_lower = []
    y = []
    data = []
    data_set = []
    PAN = 0
    temp_count = 9999
    log_file = open(vorlax_folder + "\\" + "VORLAX.LOG", 'r')
    yxdcp_upper_file = open(vorlax_folder + "\\" + "yxdcp_upper.txt", 'w')
    yxdcp_upper_fuselage_file = open(vorlax_folder + "\\" + "yxdcp_upper_fuselage.txt", 'w')
    log_lines = log_file.readlines()
    for count, log_line in enumerate(log_lines):
        # a new panel is found and data should be collected
        if "PANEL NO." in log_line:
            data = []
            temp_count = count
            collect = True
        # if data has been collected from all panels, stop collecting
        if len(data_set) == NPAN:
            collect = False
        if collect:
            if count > temp_count:
                temp_log_line = log_line.split(' ')
                temp_log_line = [x for x in temp_log_line if x]
                data.append([float(temp_log_line[2]), float(temp_log_line[3]),
                             float(temp_log_line[4]), float(temp_log_line[9])])
                if PAN % 2 == 0 and 1 < PAN < NPAN - 2:
                    if temp_log_line[1] == '1':
                        temp_log_line_lower = str(log_lines[count + 1 + int(NVOR[PAN] * RNCV[PAN])]).split(' ')
                        temp_log_line_lower = [x for x in temp_log_line_lower if x]
                        y.append(float(temp_log_line[4]))
                        cn.append(float(temp_log_line[10]) + float(temp_log_line_lower[10]))
                        cl.append(float(temp_log_line[11]) + float(temp_log_line_lower[11]))
                    if temp_log_line[1] == '5':
                        temp_log_line_lower = str(log_lines[count + 1 + int(NVOR[PAN] * RNCV[PAN])]).split(' ')
                        temp_log_line_lower = [x for x in temp_log_line_lower if x]
                        cp_upper.append(float(temp_log_line[9]))
                        cp_lower.append(float(temp_log_line_lower[9]))
                    # if the panel is a tail panel
                    # if the panel is a wing panel
                    if PAN > 1:
                        temp_yxdcp = (str(temp_log_line[3]) + "\t" + str(temp_log_line[4]) + "\t" +
                                      str(temp_log_line[9]) + "\n")
                        yxdcp_upper_file.write(temp_yxdcp)
                    # if the panel is a fuselage panel
                    if PAN == 0:
                        temp_yxdcp = (str(temp_log_line[3]) + "\t" + str(temp_log_line[4]) + "\t" +
                                      str(temp_log_line[9]) + "\n")
                        yxdcp_upper_fuselage_file.write(temp_yxdcp)
            if count == temp_count + (NVOR[PAN] * RNCV[PAN]):
                data_set.append(data)
                PAN += 1
    yxdcp_upper_file.close()
    log_file.close()

    ideal_loading = []
    actual_loading = []
    for count, coord in enumerate(y):
        ideal_loading.append(1.226 * math.sqrt(1 - (coord / (span / 2)) ** 2) * (lift / wing_area) * mean_chord)
        actual_loading.append(cn[count] * q)
    temp_error = numpy.mean([abs(ideal - actual) for ideal, actual in zip(ideal_loading, actual_loading)])
    if plot:
        pyplot.plot(y, ideal_loading)
        pyplot.plot(y, actual_loading, 'o')
        pyplot.xlabel("Spanwise Location (ft)")
        pyplot.ylabel("L' (lbf/in)")
        pyplot.show()
        ###
        pyplot.plot(y, cl, 'o', color="C0")
        pyplot.plot([-1 * temp_y for temp_y in y], cl, 'o', color="C0")
        pyplot.xlabel("Spanwise Location (in)")
        pyplot.ylabel("Coefficient of Lift")
        pyplot.show()

    PAN = 0
    critical_cp = 2 / (gamma * mach ** 2) * ((2 / (gamma + 1)) ** (gamma / (gamma - 1)) *
                                             (1 + (gamma - 1) / 2 * (mach ** 2) * (math.cos(0 * math.pi / 180) ** 2)) **
                                             (gamma / (gamma - 1)) - 1)
    for count, data in enumerate(data_set):
        # PAN += 1
        if count > 1 and PAN % 2 != 0:
            temp_x_c = []
            temp_dcp_upper = []
            temp_dcp_lower = []
            for i in range(int(RNCV[PAN])):
                temp_x_c.append(data[int(int(NVOR[PAN] / 2) * RNCV[PAN] + i)][0])
                temp_dcp_upper.append(data[int(int(NVOR[PAN] / 2) * RNCV[PAN] + i)][3])
                temp_dcp_lower.append(data_set[count + 1][int(int(NVOR[PAN] / 2) * RNCV[PAN] + i)][3])
                if min(temp_dcp_upper) < critical_cp:
                    temp_error = 9999
            if plot:
                pyplot.plot(temp_x_c, temp_dcp_upper)
                pyplot.plot(temp_x_c, temp_dcp_lower)
                pyplot.plot(temp_x_c, [critical_cp] * len(temp_x_c), '-')
                pyplot.ylim(max(temp_dcp_upper + temp_dcp_lower + [critical_cp]) + 0.5,
                            min(temp_dcp_upper + temp_dcp_lower + [critical_cp]) - 0.5)
                pyplot.xlabel("X/C")
                pyplot.ylabel("Coefficient of Pressure")
                pyplot.show()
    return temp_error


# predefining empty values
input_data = []
NPAN = 0  # number of panels in vorlax file
NVOR = []
RNCV = []
twist_index_upper = []
twist_index_lower = []
wing_area = 0  # ft^2
mach = 0
gamma = 1.4  # for air or any other diatomic gas
mean_chord = 0  # ft
span = 0  # ft

# populate predefined values from _original file
file = open(vorlax_folder + "\\" + input_file, 'r')  # open original file
lines = file.readlines()
for counter, line in enumerate(lines):
    input_data.append(line)
    temp_counter = counter + 1
    if "NMACH" in line:
        temp = lines[temp_counter].split(' ')
        temp = [x for x in temp if x]
        mach = float(temp[1])
    if "SREF" in line:
        temp = lines[temp_counter].split(' ')
        temp = [x for x in temp if x]
        NPAN = float(temp[0])
        wing_area = float(temp[1])
        mean_chord = float(temp[2])
        span = float(temp[5])
    if "NVOR" in line:
        temp = lines[temp_counter].split(' ')
        temp = [x for x in temp if x]
        NVOR.append(float(temp[0]))
        RNCV.append(float(temp[1]))
        if 2 < len(NVOR):
            if len(NVOR) % 2 != 0:
                twist_index_upper.append(counter + 3)
            else:
                twist_index_lower.append(counter + 3)
file.close()  # close _original file

# desired lift in pounds
lift = 15
# dynamic pressure at flight altitude as a function of flight mach number
q = (1481.354 * mach ** 2) / 144
# specific flight angle of attack
angle_of_attack = 2.5
# minimum error should be higher than the higher error calculated from loading distribution
minimum_error = 9999
# apply twist values or ranges of twist values to calculate error on
for i in [-1]:
    for j in [-1]:
        for k in [-1]:
            for l in [-1]:
                for m in [-1]:
                    for n in [-1]:
                        twist = [i, j, k, l, m, n, 0.0, 0.0]  # in degrees
                        twist = [round(numpy.arctan(t * math.pi / 180), 4) for t in twist]  # convert to radians
                        # call wing design function
                        error = wing_design()
                        # print out twist that provides the lowest error form loading distribution
                        if error < minimum_error:
                            output = open(vorlax_folder + r"\capstone_rc.inp.csv")
                            csv_lines = [str(line).split(',') for count, line in
                                         enumerate(output.readlines()) if count > 1]
                            calculated_lift = float(csv_lines[0][14]) * wing_area * q
                            print(calculated_lift)
                            if calculated_lift > lift:
                                minimum_error = error
                                twist = [round(numpy.tan(t) * 180 / math.pi, 4) for t in twist]
                                print(twist, error)

# [-4.9973, -1.0028, -4.9973, -4.9973, -4.9973, -4.9973, 0.0, 0.0] 0.062161057245070324
