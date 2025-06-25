from typing import Union, Tuple, Optional, Dict, List, Set

STYLE_TAG = (('', ''),
             ('<sub class="text-primary-emphasis">', '</sub>'),
             ('<sub class="text-secondary-emphasis">', '</sub>'),
             ('<sub class="text-success-emphasis">', '</sub>'),
             ('<sub class="text-info-emphasis">', '</sub>'),
             ('<sub class="text-warning-emphasis">', '</sub>'),
             ('<sub class="text-danger-emphasis">', '</sub>'),
             ('<sub class="text-light-emphasis">', '</sub>'),
             ('<sub class="text-dark-emphasis">', '</sub>'),

             ('<span class="text-primary">', '</span>'),
             ('<span class="text-secondary">', '</span>'),
             ('<span class="text-success">', '</span>'),
             ('<span class="text-info">', '</span>'),
             ('<span class="text-warning">', '</span>'),
             ('<span class="text-danger">', '</span>'),
             ('<span class="text-light">', '</span>'),
             ('<span class="text-dark">', '</span>'),

             ('<span class="text-primary-emphasis">', '</span>'),
             ('<span class="text-secondary-emphasis">', '</span>'),
             ('<span class="text-success-emphasis">', '</span>'),
             ('<span class="text-info-emphasis">', '</span>'),
             ('<span class="text-warning-emphasis">', '</span>'),
             ('<span class="text-danger-emphasis">', '</span>'),
             ('<span class="text-light-emphasis">', '</span>'),
             ('<span class="text-dark-emphasis">', '</span>')
             )


def key_design(key: str, change_style: bool = True, style: int = 6) -> str:
    style_tag = STYLE_TAG[style] if change_style else STYLE_TAG[0]
    return f'{style_tag[0]}{key.replace("_", " ")}:\t{style_tag[1]}'


def value_design(value: Optional[Union[str, Tuple[str, ...], List[str], Set[str]]], change_style: bool = True,
                 style: int = 4) -> str:
    if isinstance(value, (tuple, list, set)):
        return "".join([value_design("<p>" + i + "</p>", True, 5) for i in value])
    style_tag = STYLE_TAG[style] if change_style else STYLE_TAG[0]
    return f'{style_tag[0]}{value}{style_tag[1]}'


def dna_design(dna: str, different_color: Optional[Tuple[int, int]] = None, styles: Tuple[int, int] = (14, 13)) -> str:
    style_tag = STYLE_TAG[styles[0]] + STYLE_TAG[styles[1]]
    start = False
    start_dc = False
    str_result = ''
    for i in enumerate(dna):
        if different_color and different_color[0] == i[0]:
            j = f'{style_tag[2]}{i[1]}'
            start_dc = True
        elif i[1].upper() != i[1] and not start and not start_dc:
            j = f'{style_tag[0]}{i[1]}'
            start = True
        elif i[1].upper() == i[1] and start and not start_dc:
            j = f'{style_tag[1]}{i[1]}'
            start = False
        else:
            j = i[1]

        if different_color and different_color[1] == i[0]+1:
            j += f'{style_tag[3]}'
            start_dc = False

        str_result += j

    return f'<b>{str_result}</b>'


def result_design(data: Dict[str, Union[str, int, float]], change_key: bool = True, change_value: bool = True
                  ) -> Dict[str, Union[str, int, float]]:

    for key, value in data.items():
        data.update({key: value_design(str(value), change_value)})
    return data
#
#
# def result_design(statistics: Union[Dict[str, Union[str, int, float]], List[Dict[str, Union[str, int, float]]]],
#                   change_key: bool = True, change_value: bool = True) -> str:
#     result = ''
#
#     for key, value in statistics.items():
#         result += f'{key_design(key, change_key)}{value_design(str(value), change_value)}<br>'
#     return f'<b>{result}</b>'
