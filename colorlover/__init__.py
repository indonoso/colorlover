import colorsys
from collections import defaultdict
import math
from .scales import scales


def scale_type(scale):
    ''' returns "rbg", "hsl", "numeric", or raises exception. ie,
        [ "rgb(255, 255, 255)", "rgb(255, 255, 255)", "rgb(255, 255, 255)" ] --> "rgb" '''
    swatch = scale[0]
    s_t = str(swatch)[0:3]
    if s_t in ['rgb', 'hsl']:
        return s_t
    elif isinstance(swatch, tuple) and len(swatch) == 3:
        return 'numeric'
    raise Exception('Could not determine type of input colorscale.\n\
Colorscales must be in one of these 3 forms:\n\
[ (255, 255, 255), (255, 255, 255), (255, 255, 255) ]\n\
[ "rgb(255, 255, 255)", "rgb(255, 255, 255)", "rgb(255, 255, 255)" ]\n\
[ "hsl(360,100,100)", "hsl(360,100,100)", "hsl(360,100,100)" ]')


def to_numeric(scale):
    ''' converts scale of rgb or hsl strings to list of tuples with rgb integer values. ie,
        [ "rgb(255, 255, 255)", "rgb(255, 255, 255)", "rgb(255, 255, 255)" ] -->
        [ (255, 255, 255), (255, 255, 255), (255, 255, 255) ] '''
    numeric_scale = []
    s_t = scale_type(scale)
    if s_t in ['rgb', 'hsl']:
        for s in scale:
            s = s[s.find("(") + 1:s.find(")")].replace(' ', '').split(',')
            numeric_scale.append((float(s[0]), float(s[1]), float(s[2])))
    elif s_t == 'numeric':
        numeric_scale = scale
    return numeric_scale


def to_hsl(scale):
    ''' convert a string rgb or numeric rgb colorscale to hsl. ie,
        [ "rgb(255, 255, 255)", "rgb(255, 255, 255)", "rgb(255, 255, 255)" ] -->
        [ "hsl(360,100%,100%)", "hsl(360,100%,100%)", "hsl(360,100%,100%)" ]
        add percentages to saturation and lightness if missing for css compatibility '''

    hsl = []
    s_t = scale_type(scale)

    if s_t == 'hsl':
        # add percentages to s and l if missing

        numeric_hsl_scale = []
        for s in scale:
            s = s[s.find("(") + 1:s.find(")")].replace(' ', '').replace('%', '').split(',')
            numeric_hsl_scale.append((float(s[0]), float(s[1]), float(s[2])))

        for ea in numeric_hsl_scale:
            h, s, l = [str(x) for x in ea]
            if s[-1] != '%':
                s = s + '%'
            if l[-1] != '%':
                l = l + '%'
            hsl_str = 'hsl(' + ', '.join([h, s, l]) + ')'
            hsl.append(hsl_str)

        return hsl

    elif s_t == 'rgb':
        scale = to_numeric(scale)

    for ea in scale:
        r, g, b = [x / 255.0 for x in ea]
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        h, s, l = [str(int(round(h * 360.0))), str(int(round(s * 100.0))) + '%', str(int(round(l * 100.0))) + '%']
        hsl_str = 'hsl(' + ', '.join([h, s, l]) + ')'
        hsl.append(hsl_str)

    return hsl


def to_rgb(scale):
    ''' convert an hsl or numeric rgb color scale to string rgb color scale. ie,
        [ "hsl(360,100,100)", "hsl(360,100,100)", "hsl(360,100,100)" ] -->
        [ "rgb(255, 255, 255)", "rgb(255, 255, 255)", "rgb(255, 255, 255)" ]
        '''

    rgb = []
    s_t = scale_type(scale)

    if s_t == 'rgb':
        return scale
    elif s_t == 'numeric':
        for ea in scale:
            rgb.append('rgb' + str(ea))
        return rgb
    elif s_t == 'hsl':
        numeric_hsl_scale = []
        for s in scale:
            s = s[s.find("(") + 1:s.find(")")].replace(' ', '').replace('%', '').split(',')
            numeric_hsl_scale.append((float(s[0]), float(s[1]), float(s[2])))
        scale = numeric_hsl_scale

    for ea in scale:
        h, s, l = [float(x) for x in ea]
        r, g, b = colorsys.hls_to_rgb(h / 360.0, l / 100.0, s / 100.0)
        r, g, b = [str(int(round(x * 255.0))) for x in (r, g, b)]
        rgb_str = 'rgb(' + ', '.join([r, g, b]) + ')'
        rgb.append(rgb_str)

    return rgb


def to_html(scale):
    ''' traverse color scale dictionary and return available color scales in HTML string '''

    global s
    s = ''

    def single_scale(scale):
        ''' return square html <div> for a single color '''
        if scale_type(scale) == 'numeric':
            scale = to_rgb(scale)
        s_s = ''
        for ea in scale:
            s_s += '<div style="background-color:{0};height:20px;width:20px;display:inline-block;"></div>'.format(ea)
        return s_s

    def section_titles(k):
        d = {'qual': 'Qualitative', 'div': 'Diverging', 'seq': 'Sequential'}
        if k in list(d.keys()):
            return '<h4>' + d[k] + '</h4>'
        return '<hr><h3>' + k + ' colors</h3>'

    def prettyprint(d):
        global s
        for k, v in list(d.items()):
            if isinstance(v, dict):
                if len(list(v.keys())) != 0:
                    s += section_titles(k)
                prettyprint(v)
            else:
                s += '<div style="display:inline-block;padding:10px;"><div>{0}</div>{1}</div>'.format(k,
                                                                                                      single_scale(v))
        return s

    if isinstance(scale, list):
        return single_scale(scale)
    elif isinstance(scale, dict):
        prettyprint(scale)

    return s


def flipper(scl=None):
    ''' Invert color scale dictionary '''
    scl = scl if scl is not None else scales
    flipped = defaultdict(dict)
    for key, val in list(scl.items()):
        for subkey, subval in list(val.items()):
            flipped[subkey][key] = subval
    return flipped


def interp(scl, r):
    ''' Interpolate a color scale "scl" to a new one with length "r"
        Fun usage in IPython notebook:
        HTML( to_html( to_hsl( interp( cl.scales['11']['qual']['Paired'], 5000 ) ) ) ) '''
    c = []
    SCL_FI = len(scl) - 1  # final index of color scale
    # garyfeng:
    # the following line is buggy.
    # r = [x * 0.1 for x in range(r)] if isinstance( r, int ) else r
    r = [x * 1.0 * SCL_FI / r for x in range(r)] if isinstance(r, int) else r
    # end garyfeng

    scl = to_numeric(scl)

    def interp3(fraction, start, end):
        ''' Interpolate between values of 2, 3-member tuples '''

        def intp(f, s, e):
            return s + (e - s) * f

        return tuple([intp(fraction, start[i], end[i]) for i in range(3)])

    def rgb_to_hsl(rgb):
        ''' Adapted from M Bostock's RGB to HSL converter in d3.js
            https://github.com/mbostock/d3/blob/master/src/color/rgb.js '''
        r, g, b = float(rgb[0]) / 255.0, \
                  float(rgb[1]) / 255.0, \
                  float(rgb[2]) / 255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        h = s = l = (mx + mn) / 2
        if mx == mn:  # achromatic
            h = 0
            s = 0 if l > 0 and l < 1 else h
        else:
            d = mx - mn;
            s = d / (mx + mn) if l < 0.5 else d / (2 - mx - mn)
            if mx == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif mx == g:
                h = (b - r) / d + 2
            else:
                h = r - g / d + 4

        return (int(round(h * 60, 4)), int(round(s * 100, 4)), int(round(l * 100, 4)))

    for i in r:
        # garyfeng: c_i could be rounded up so scl[c_i+1] will go off range
        # c_i = int(i*math.floor(SCL_FI)/round(r[-1])) # start color index
        # c_i = int(math.floor(i*math.floor(SCL_FI)/round(r[-1]))) # start color index
        # c_i = if c_i < len(scl)-1 else hsl_o

        c_i = int(math.floor(i))
        section_min = math.floor(i)
        section_max = math.ceil(i)
        fraction = (i - section_min)  # /(section_max-section_min)

        hsl_o = rgb_to_hsl(scl[c_i])  # convert rgb to hls
        hsl_f = rgb_to_hsl(scl[c_i + 1])
        # section_min = c_i*r[-1]/SCL_FI
        # section_max = (c_i+1)*(r[-1]/SCL_FI)
        # fraction = (i-section_min)/(section_max-section_min)
        hsl = interp3(fraction, hsl_o, hsl_f)
        c.append('hsl' + str(hsl))

    return to_hsl(c)
