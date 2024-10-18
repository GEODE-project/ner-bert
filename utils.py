

def filter_tags(sentence, tagset, remove_nested=False):
    result = [['O']] * len(sentence['tokens'])
    for span in sentence['spans']:
        if(span['label'] in tagset):
            for i in range(span['token_start'], span['token_end']+1):
                if(result[i] == ['O']):
                    result[i] = [span['label']]
                else:
                    result[i].append(span['label'])
                    result[i] = sorted(result[i])
    if(remove_nested):
        for i in range(len(result)):
            if(len(result[i]) > 1):
                result[i] = [result[i][0]]
    return result


def format(content, tags_id):
    return list(map(lambda x: tags_id[x], content))


def get_data(d):
    data = []
    for content in d:
        data.append({'tokens': [token['text'] for token in content['tokens']], 'tags_id': content['ids']})
    return data

