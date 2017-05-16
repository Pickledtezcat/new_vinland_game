import bge
import mathutils


class GeneralMessage(object):
    def __init__(self, header, content=None):
        self.header = header
        self.content = content


def sound_message(header, content=None):
    bge.logic.globalDict["sounds"].append({"header": header, "content": content})


def get_key(position):
    return "{}${}".format(int(round(position[0])), int(round(position[1])))


def smoothstep(x):
    return x * x * (3 - 2 * x)


def get_distance(a, b):
    vector = mathutils.Vector(b).to_3d() - mathutils.Vector(a).to_3d()
    return vector.length


def get_ob(string, ob_list):
    ob_list = [ob for ob in ob_list if string in ob]
    if ob_list:
        return ob_list[0]


def get_ob_list(string, ob_list):
    ob_list = [ob for ob in ob_list if string in ob]

    return ob_list


def interpolate_float(current, target, factor):

    return (current * (1.0 - factor)) + (target * factor)


def diagonal(location):
    x, y = location
    if abs(x) - abs(y) == 0:
        return True


def split_in_lines(contents, line_length, center=False):

    new_lines = []

    split_lines = contents.splitlines()
    for line in split_lines:
        words = line.split()

        if len(words) == 1:
            short_length = max(2, line_length - 2)

            if len(words[0]) > short_length:
                return "{}-\n{}".format(words[0][:short_length], words[0][short_length:])

        new_line = []
        lines = []
        letters = 0

        for word in words:
            letters += len(word)

            if letters < line_length:
                new_line.append(word)
            else:
                lines.append(" ".join(new_line))
                new_line = [word]
                letters = len(word)

        if new_line:
            lines.append(" ".join(new_line))

        if center:
            lines = ["{:^{length}}".format(line, length=line_length) for line in lines]

        new_contents = "\n".join(lines)
        new_lines.append(new_contents)

    return "\n".join(new_lines)