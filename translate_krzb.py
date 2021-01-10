def tr(txt):
    if txt is None: return "чего переводить-то?"
    tr_dict = {
            'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
             'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы',
             'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д',
             ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и',
             'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.', '&': '?', '`': 'ё', 
             '~': 'ё', '>': 'ю', '<': 'б'
            }
    def t(x):        
        if x in tr_dict:
            x = tr_dict.get(x)
        return x    
    
    txt_list = list()
    txt_tuple = tuple(txt)
    for i in txt_tuple:
        y = t(i.lower())
        txt_list.append(y)
    res = ''.join(txt_list)
    return res
   
