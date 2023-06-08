# st_ACT_202106.py

# The blank {tc} ACT scoring table as a python dict. After filling
# in the ranges, run the file in a session to load the scoring table
# in a namespace:

# exec( open('st_ACT_123456.py').read() )
#


scoring_table = {
    'test_code':202106,
    'table':{
        1:{'e':range(0,2), 'm':range(0,1), 'r':range(0,1), 's':range(0,1)},
        2:{'e':range(2,3), 'm':range(0,0), 'r':range(1,2), 's':range(0,0)},
        3:{'e':range(3,5), 'm':range(0,0), 'r':range(0,0), 's':range(1,2)},
        4:{'e':range(5,6), 'm':range(1,2), 'r':range(2,3), 's':range(0,0)},
        5:{'e':range(6,8), 'm':range(0,0), 'r':range(3,4), 's':range(2,3)},
        6:{'e':range(8,10), 'm':range(2,3), 'r':range(0,0), 's':range(0,0)},
        7:{'e':range(10,12), 'm':range(0,0), 'r':range(4,5), 's':range(3,4)},
        8:{'e':range(12,14), 'm':range(3,4), 'r':range(5,6), 's':range(4,5)},
        9:{'e':range(14,16), 'm':range(4,5), 'r':range(6,7), 's':range(5,6)},
        10:{'e':range(16,20), 'm':range(5,6), 'r':range(7,8), 's':range(6,7)},
        11:{'e':range(20,23), 'm':range(6,7), 'r':range(8,10), 's':range(7,8)},
        12:{'e':range(23,25), 'm':range(7,8), 'r':range(10,11), 's':range(8,9)},
        13:{'e':range(25,27), 'm':range(8,10), 'r':range(11,13), 's':range(9,10)},
        14:{'e':range(27,29), 'm':range(10,13), 'r':range(13,14), 's':range(10,11)},
        15:{'e':range(29,32), 'm':range(13,16), 'r':range(14,16), 's':range(11,12)},
        16:{'e':range(32,35), 'm':range(16,19), 'r':range(16,17), 's':range(12,14)},
        17:{'e':range(35,37), 'm':range(19,22), 'r':range(17,19), 's':range(14,16)},
        18:{'e':range(37,39), 'm':range(22,25), 'r':range(19,20), 's':range(16,18)},
        19:{'e':range(39,41), 'm':range(25,27), 'r':range(20,21), 's':range(18,19)},
        20:{'e':range(41,44), 'm':range(27,28), 'r':range(21,23), 's':range(19,21)},
        21:{'e':range(44,48), 'm':range(28,30), 'r':range(23,24), 's':range(21,23)},
        22:{'e':range(48,51), 'm':range(30,31), 'r':range(24,26), 's':range(23,24)},
        23:{'e':range(51,54), 'm':range(31,33), 'r':range(26,27), 's':range(24,26)},
        24:{'e':range(54,57), 'm':range(33,36), 'r':range(27,29), 's':range(26,28)},
        25:{'e':range(57,60), 'm':range(36,38), 'r':range(29,30), 's':range(28,30)},
        26:{'e':range(60,61), 'm':range(38,41), 'r':range(30,31), 's':range(30,32)},
        27:{'e':range(61,63), 'm':range(41,44), 'r':range(0,0), 's':range(32,33)},
        28:{'e':range(63,64), 'm':range(44,47), 'r':range(31,32), 's':range(33,34)},
        29:{'e':range(64,66), 'm':range(47,49), 'r':range(32,33), 's':range(34,35)},
        30:{'e':range(66,67), 'm':range(49,51), 'r':range(33,34), 's':range(35,36)},
        31:{'e':range(67,68), 'm':range(51,52), 'r':range(34,35), 's':range(36,37)},
        32:{'e':range(68,69), 'm':range(52,54), 'r':range(35,36), 's':range(0,0)},
        33:{'e':range(69,70), 'm':range(54,55), 'r':range(36,37), 's':range(37,38)},
        34:{'e':range(70,71), 'm':range(55,57), 'r':range(37,38), 's':range(38,39)},
        35:{'e':range(71,74), 'm':range(57,59), 'r':range(38,39), 's':range(39,40)},
        36:{'e':range(74,76), 'm':range(59,61), 'r':range(39,41), 's':range(40,41)}
    }
}
