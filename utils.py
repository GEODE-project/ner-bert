

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


def get_teicorpus_header(meta):
    #header = '<?xml version="1.0" encoding="UTF-8"?>'
    header = "<teiCorpus>"
    header += "<teiHeader>"
    header += "<fileDesc>"
    header += "<titleStmt>"
    header += f"<title>{meta['book']}</title>"
    header += "<respStmt>"
    header += "<resp>Digitized by</resp>"
    header += "<orgName>University of Chicago Library</orgName>"
    header += "</respStmt>"
    header += "<respStmt>"
    header += "<resp>Published by</resp>"
    header += "<orgName>ARTFL</orgName>"
    header += "</respStmt>"
    header += "<respStmt>"
    header += "<resp>Annotated and encoded by</resp>"
    header += "<orgName>GEODE project - https://geode-project.github.io </orgName>"
    header += "<name>Denis Vigier - https://www.icar.cnrs.fr/membre/dvigier </name>"
    header += "<name>Ludovic Moncla - https://ludovicmoncla.github.io </name>"
    header += "</respStmt>"
    header += "</titleStmt>"
    header += "<publicationStmt>"
    header += "<distributor>"
    header += "<orgName>GEODE project - https://geode-project.github.io </orgName>"
    header += "<name>Denis Vigier - https://www.icar.cnrs.fr/membre/dvigier/ </name>"
    header += "<name>Ludovic Moncla - https://ludovicmoncla.github.io </name>"
    header += "</distributor>"
    header += "</publicationStmt>"
    header += "<sourceDesc>"
    header += "<bibl>"
    header += f"<title>L'Encyclopédie T{meta['tome']}</title>"
    header += "<author>Collective</author>"
    header += "<creation>"
    header += "<date>1752</date>"
    header += "</creation>"
    header += "</bibl>"
    header += "</sourceDesc>"
    header += "</fileDesc>"
    header += "</teiHeader>"
    return header


def get_teicorpus_footer():
    footer = "</teiCorpus>"
    return footer


def get_tei_header(meta):
    header = "<TEI>"
    header += "<teiHeader>"
    header += "<fileDesc>"
    header += "<titleStmt>"
    header += f"<title>{meta['head']}</title>"
    header += "</titleStmt>"
    header += "<publicationStmt>"
    header += "<p>Annotated with Spacy (fr_dep_news_trf) and https://huggingface.co/GEODE/camembert-base-edda-span-classification by project GEODE</p>"
    header += "</publicationStmt>"
    header += "<sourceDesc>"
    header += "<bibl>"
    header += f"<author>{meta['author'][1:-1]}</author>"
    header += "</bibl>"
    header += "</sourceDesc>"
    header += "</fileDesc>"
    header += "</teiHeader>"
    return header


def get_tei_footer():
    footer = "</TEI>"
    return footer


def spacy_to_xml(doc, meta=None):
    if meta is None:
        xml = "<text>" # <text uid="EDdA_1_6" book="EDdA" author=":Dumarsais5:" domains=":Philosophie:">
    else:
        xml = get_tei_header(meta)
        xml += "<text "
        for key, value in meta.items():
            if key == "head" or key == "volume":
                continue
            xml += f"{key}='{value}' "
        xml += ">"
        
    xml += "<body>"
    for sent in doc.sents:
        xml += "<s>"
        for w in sent:
            xml += f"<w lemma='{w.lemma_}' pos='{w.pos_}' start='{w.idx}' end='{w.idx + len(w.text)}'>{w.text}</w>"
        xml += "</s>"
    xml += '</body><milestone unit="article"/></text>'
    if meta is not None:
        xml += get_tei_footer()
    return xml


def merge_annotations(root, annotations):

    for ann in annotations:
        start = str(ann['start'])
        end = str(ann['end'])
        word = ann['word']
        tag = ann['entity_group']
        #print(f"start: {start}, end: {end}, word: {word}, tag: {tag}")
        matches = root.xpath('//w[@start="'+start+'" and @end="'+end+'"]')

        if not matches:
            m = root.xpath('//w[@start="'+start+'"]')
            if not m:
                print("No match found.")
            elif len(matches) > 1:
                raise ValueError("Multiple matches found.")
            else:
                w = m[0]
                w.set("type", "B-"+tag)
                br = False
                # get m sibling
                for sibling in w.itersiblings():
                    if sibling.get("end") == end:
                        sibling.set("type", "E-"+tag)
                        br = True
                        break
                    else:
                        if sibling.get("end") < end and sibling.get("start") > start:
                            sibling.set("type", "I-"+tag)

                if not br:
                    m = root.xpath('//w[@end="'+end+'"]') 
                    if not m:
                        print("No match found.")
                    elif len(matches) > 1:
                        raise ValueError("Multiple matches found.")
                    else:
                        w = m[0]
                        w.set("type", "E-"+tag)
                        for sibling in w.itersiblings(preceding=True):
                            if sibling.get("end") < end and sibling.get("start") > start:
                                sibling.set("type", "I-"+tag)
                # I ?
                # E ?

        elif len(matches) > 1:
            raise ValueError("Multiple matches found.")
        else:
            w = matches[0]
            w.set("type", "S-"+tag)
            #print("Unique match:")

        # parse the xml with xpath to find the w element with the corresponding start and end of the word (potentially multiple)

        #xml = xml[:start] + f"<{tag}>" + xml[start:end] + f"</{tag}>" + xml[end:]
    return root