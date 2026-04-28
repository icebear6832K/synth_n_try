digi_s = '𝟢𝟣𝟤𝟥𝟦𝟧𝟨𝟩𝟪𝟫'
digi_b = '𝟎𝟏𝟐𝟑𝟒𝟓𝟔𝟕𝟖𝟗'
digi_c = '𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵'
digi_x = '𝟘𝟙𝟚𝟛𝟜𝟝𝟞𝟟𝟠𝟡'
digi_z = '𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿'
digi_m = '₀₁₂₃₄₅₆₇₈₉'
digi_u = '⁰¹²³⁴⁵⁶⁷⁸⁹'


def digit_show(num, f_type='s'):
    str_num = ''
    for c in str(num):
        if c in '0123456789':
            if f_type == 's':
                str_num += digi_s[int(c)]
            elif f_type == 'b':
                str_num += digi_b[int(c)]
            elif f_type == 'c':
                str_num += digi_c[int(c)]
            elif f_type == 'm':
                str_num += digi_m[int(c)]
            elif f_type == 'x':
                str_num += digi_x[int(c)]
            elif f_type == 'z':
                str_num += digi_z[int(c)]
            elif f_type == 'u':
                str_num += digi_u[int(c)]
        else:
            str_num += c
    return str_num

