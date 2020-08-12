import re
import time

import requests
import lxml.html
import rdflib
import sys
from rdflib import Literal, XSD

ontology_prefix = "http://en.wikipedia.org/"
wiki_prefix = "http://en.wikipedia.org"


#############################################################################################
#
#                                  Create Ontology:
#
#############################################################################################
def get_relevant_text(texts, field, country_name):
    try:
        if type(texts) != list:
            texts = [texts]
        # max filtered
        texts_filtered = [text for text in texts if
                          field.lower() not in text.lower() and
                          field.replace(" ", "_").lower() not in text.lower() and
                          country_name.lower() not in text.lower() and
                          "list_of" not in text.lower() and
                          "General_Secretary_of".lower() not in text.lower() and
                          '#cite_note-2'.lower() not in text.lower() and
                          "file:" not in text.lower()]
        if texts_filtered:
            text = texts_filtered[0].split("/wiki/")[-1]
            text = text.strip()
            if "(" in text:
                text = text.split("(")[0]
            text = text.replace(" ", "_")
            text = text.replace(u"\xa0", "_")
            return text

        # try filter again
        texts_filtered = [text for text in texts if
                          field.lower() not in text.lower() and
                          field.replace(" ", "_").lower() not in text.lower() and
                          "(%s)" % country_name.lower() not in text.lower() and
                          "list_of" not in text.lower() and
                          "file:" not in text.lower()]
        if texts_filtered:
            text = texts_filtered[0].split("/wiki/")[-1]
            text = text.strip()
            if "(" in text:
                text = text.split("(")[0]
            text = text.replace(" ", "_")
            text = text.replace(u"\xa0", "_")
            return text

        # try filter again
        texts_filtered = [text for text in texts if
                          field.lower() not in text.lower() and
                          field.replace(" ", "_").lower() not in text.lower() and
                          "list_of" not in text.lower() and
                          "file:" not in text.lower()]
        if texts_filtered:
            text = texts_filtered[0].split("/wiki/")[-1]
            text = text.strip()
            if "(" in text:
                text = text.split("(")[0]
            text = text.replace(" ", "_")
            text = text.replace(u"\xa0", "_")
            return text

        # try filter again
        texts_filtered = [text for text in texts if
                          "list_of" not in text.lower() and
                          "file:" not in text.lower()]
        if texts_filtered:
            text = texts_filtered[0].split("/wiki/")[-1]
            text = text.strip()
            if "(" in text:
                text = text.split("(")[0]
            text = text.replace(" ", "_")
            text = text.replace(u"\xa0", "_")
            return text

        # not found
        return None
    except Exception as e:
        print(e)
        exit()


def get_relevant_text_with_sup(texts, field, country_name, sup):
    try:
        text = get_relevant_text(texts, field, country_name)
        if text and len(sup) > 1 and ("(" not in text):
            if "km" in text and sup[1].isdigit():
                return text + sup[1]
            else:
                for t in sup:
                    if "[" and "]" in t:
                        continue
                    if "km" not in text and "km" in t:
                        text = text + "_" + t
                    if "km" in text and t.isdigit():
                        text = text + t
                        break
        if "km" not in text or not text[-1].isdigit():
            for t in sup:
                ts = t.split(" ")
                for i in ts:
                    matches = re.findall("\d+,\d+,*\d+\s+km", i)
                    if matches:
                        text = matches[0].replace(" ", "_").replace(u"\xa0", "_") + "2"
                        return text
        return text
    except Exception as e:
        print(e)
        exit()


def get_field_capital(info_box, field, country_name):
    try:
        b = info_box.xpath(f"(//table//tr[th[text() = '{field}']]/td[1])[1]//text()")
        val = None
        if b:
            if country_name == 'Switzerland':
                return b[4]  # bern
            while not val or val == '_' and len(b) > 0:
                text = b[0]
                if "(" in text:  # removes ()
                    text = text.split("(")[0]
                text = text.replace("\n", "")
                if text == " ":
                    text = None
                b = b[1:]
                val = text
            if val:
                val = val.replace(" ", "_")
                return val
        return None
    except Exception as e:
        print(e)
        exit()


def get_field_president_prime(info_box, field, country_name):
    try:
        country_name = country_name.lower().replace(" ", "_")
        url = None
        birth_date = None
        b = info_box.xpath(f"//table//th[text() = '{field}']")
        if b:
            # get the entity name from the url
            texts = b[0].xpath("../*/a/@href")
            text = get_relevant_text(texts, field, country_name)
            if not text:
                texts = b[0].xpath("..//a/@href")[0]
                text = get_relevant_text(texts, field, country_name)
                if not text:
                    texts = b[0].xpath("./../td//a/@href")
                    text = get_relevant_text(texts, field, country_name)
                    if not text:
                        return None, None
            for t in texts:
                if text in t and "/wiki/" in t:
                    url = t
                    break
            if text and url:
                birth_date = get_birth_date(url)
            if text and "cite_note" in text:
                return None, None
            return text, birth_date
        else:
            b = info_box.xpath(f"//table//th//*[text() = '{field}']")
            if b:
                texts = b[0].xpath("../../..//a/@href")
                text = get_relevant_text(texts, field, country_name)
                if not text:
                    b = info_box.xpath(f"(//table//tr[th[.//*[text() = '{field}']]]/td[1])[1]//a/@href")
                    if b:
                        text = get_relevant_text(b, field, country_name)
                        if not text:
                            b = info_box.xpath(f"(//table//tr[th[text() = '{field}']]/td[1])[1]//a/@href")
                            if b:
                                text = get_relevant_text(b, field, country_name)
                                if not text:
                                    return None, None
                if text:
                    for t in texts:
                        if text in t and "/wiki/" in t:
                            url = t
                            break
                if text and not url:
                    url = "/wiki/" + text
                if text and url:
                    birth_date = get_birth_date(url)
                if text and "cite_note" in text:
                    return None, None
                return text, birth_date

            else:
                return None, None
    except Exception as e:
        print(e)
        exit()


def get_field_birth_date(info_box):
    try:
        field = "Born"
        b = info_box.xpath(f"(//table//tr[th[.//*[text() = '{field}']]]/td[1])[1]//text()")
        if not b:
            b = info_box.xpath(f"(//table//tr[th[text() = '{field}']]/td[1])[1]//text()")
        if not b:
            return None
        texts = [text.replace(" ", "_") for text in b if not str.isspace(text) and not ("[" in text and "]" in text)]
        if texts:
            text = "_".join(texts)
            text = text.replace("\n", "")
            return text
        return None
    except Exception as e:
        print(e)
        exit()


def get_birth_date(url):
    try:
        url = wiki_prefix + url
        date = None
        month_dict = {"january": "01",
                      "february": "02",
                      "march": "03",
                      "april": "04",
                      "may": "05",
                      "june": "06",
                      "july": "07",
                      "august": "08",
                      "september": "09",
                      "october": "10",
                      "november": "11",
                      "december": "12"
                      }
        res = requests.get(url)
        doc = lxml.html.fromstring(res.content)
        try:
            info_box = doc.xpath("//table[contains(@class, 'infobox')]")[0]
        except Exception as e:
            print(e)
            exit()

        text = get_field_birth_date(info_box)
        if not text:
            return None
        # full date
        matches = re.findall("\d\d\d\d-\d\d-\d\d", text)
        if matches:
            date = matches[0]
        else:
            matches = re.findall("\d+_\w+_\d\d\d\d", text)
            if matches:
                m = matches[0]
                parts = m.split("_")
                day = parts[0]
                month = month_dict[parts[1].strip().lower()]
                year = parts[2]
                date = "%s-%s-%s" % (year, month, day)
            else:
                # only year
                matches = re.findall("\d\d\d\d", text)
                if matches:
                    return None

        return date
    except Exception as e:
        print(e)
        exit()


def get_field_population(info_box, field, country_name):
    try:
        country_name = country_name.lower().replace(" ", "_")
        if country_name == "channel_islands":  # population in the same row
            b = info_box.xpath(f"//table//\
                        tr[.//th[contains(text(), '{field}')]]/td/text()[1]")
            if b:
                texts = [text for text in b if not str.isspace(text) and str.isdigit(text.strip()[0])]
                if texts:
                    text = texts[0]
                    return text
                if not texts:
                    return None
            else:
                return None
        b = info_box.xpath(f"//table//tr[th[.//*[text() = '{field}']]]/following-sibling\
                ::tr[1]/td/text()[1]")
        if b and str.isdigit(b[0].strip()[0]):
            # get the entity name from the url
            texts = b
            text = get_relevant_text(texts, field, country_name)
            if not text:
                texts = b[0].xpath("..//a/@href")[0]
                text = get_relevant_text(texts, field, country_name)
                if not text:
                    texts = b[0].xpath("./../td//a/@href")
                    text = get_relevant_text(texts, field, country_name)
                    if not text:
                        return None
            return text
        else:
            b = info_box.xpath(f"//table//tr[th[.//*[text() = '{field}']]]/following-sibling\
                        ::tr[1]/td[1]//text()")
            if b:
                texts = [text for text in b if not str.isspace(text) and str.isdigit(text.strip()[0])]
                if texts:
                    text = texts[0]
                    return text
                if not texts:
                    return None
            else:
                b = info_box.xpath(f"//table//\
                           tr[.//th[contains(text(), '{field}')]]/following-sibling::tr[1]/td/text()[1]")
                if b:
                    texts = [text for text in b if not str.isspace(text) and str.isdigit(text.strip()[0])]
                    if texts:
                        text = texts[0]
                        return text
                    if not texts:
                        return None
                else:
                    return None
    except Exception as e:
        print(e)
        exit()


def get_population(info_box, field, country_name):
    try:
        population = get_field_population(info_box, field, country_name)
        population = population.replace("_", "").strip()
        if "(" in population:
            population = population.split("(")[0]
        if not re.match("\d+(?:,\d*)*\.*\d*", str(population)):
            return None
        return population
    except Exception as e:
        print(e)
        exit()


def get_field_government(info_box, field):
    try:
        b = info_box.xpath(f"(//table//tr[th[.//*[text() = '{field}']]]/td[1])[1]//text()")
        if not b:
            b = info_box.xpath(f"(//table//tr[th[text() = '{field}']]/td[1])[1]//text()")
        if not b:
            return None
        texts = [text.replace(" ", "_") for text in b if not str.isspace(text) and not ("[" in text and "]" in text)]
        if texts:
            text = "_".join(texts)
            text = re.sub("[\(\[].*?[\)\]]", "", text)
            text = text.replace("\n", "")
            while "__" in text:
                text = text.replace("__", "_")
            while text.startswith("_"):
                text = text[1:]
            while text.endswith("_"):
                text = text[:-1]
            return text
        return None
    except Exception as e:
        print(e)
        exit()


def get_field_area(info_box, field, country_name):
    try:
        country_name = country_name.lower().replace(" ", "_")
        b = info_box.xpath(f"//table//tr[th[.//*[text() = '{field}']]]/following-sibling\
                ::tr[1]/td/text()[1]")
        sup = info_box.xpath(f"//table//tr[th[.//*[text() = '{field}']]]/following-sibling\
                    ::tr[1]/td//text()")
        if b and str.isdigit(b[0].strip()[0]):
            texts = b
            text = get_relevant_text_with_sup(texts, field, country_name, sup)
            if not text:
                texts = b[0].xpath("..//a/@href")[0]
                text = get_relevant_text_with_sup(texts, field, country_name, sup)
                if not text:
                    texts = b[0].xpath("./../td//a/@href")
                    text = get_relevant_text_with_sup(texts, field, country_name, sup)
                    if not text:
                        return None
            return text
        else:
            b = info_box.xpath(f"//table//tr[th[.//*[text() = '{field}']]]/following-sibling\
                            ::tr[1]/td[1]//text()")
            if b:
                texts = [text for text in b if not str.isspace(text) and str.isdigit(text.strip()[0])]
                if texts:
                    text = texts[0]
                    return text
                if not texts:
                    return None
            else:
                b = info_box.xpath(f"//table//\
                               tr[.//th[contains(text(), '{field}')]]/following-sibling::tr[1]/td/text()[1]")
                if b:
                    texts = [text for text in b if not str.isspace(text) and str.isdigit(text.strip()[0])]
                    if texts:
                        text = texts[0]
                        return text
                    if not texts:
                        return None
                else:
                    b = info_box.xpath(f"//table//tr[.//th[text() = '{field}']]/td/text()[1]")
                    texts = [text for text in b if not str.isspace(text) and str.isdigit(text.strip()[0])]
                    if texts:
                        text = texts[0]
                        return text
                    if not texts:
                        return None
    except Exception as e:
        print(e)
        exit()


def get_area(info_box, country_name):
    try:
        area = get_field_area(info_box, field='Area ', country_name=country_name)
        if area and country_name.lower() not in ["ecuador", "algeria"]:
            area = area.strip()
            area = area.replace(" ", "_").replace(u"\xa0", "")
            if "(" in area:
                area = area.split("(")[1]
            if not re.match("\d+(?:,\d*)*\.*\d*_km2", area):
                if re.match("\d+(?:,\d*)*\.*\d*", area) and "km2" not in area:
                    area = area + "_km2"
                elif re.match("\d+(?:,\d*)*\.*\d*_km", area):
                    area = area + "2"
                elif re.match("\d+(?:,\d*)*\.*\d*km2", area):
                    area = area[:-3] + "_km2"
            if not re.match("\d+(?:,\d*)*\.*\d*_km2", area):
                if "–" in area:
                    if not re.match("\d+(?:,\d*)*\.*\d*_km2", area.split("–")[-1]):
                        return None
                else:
                    return None
        else:
            area = get_field_area(info_box, field='Area', country_name=country_name)
            if not area:
                return None
            if "(" in area:
                area = area.split("(")[-1]
            if area[-2:] == "km":
                area = area[:-2]
            area = area.replace(" ", "").replace(u"\xa0", "")
            if not re.match("\d+(?:,\d*)*\.*\d*_km2", area):
                if re.match("\d+(?:,\d*)*\.*\d*km2", area):
                    area = area[:-3] + "_km2"
                elif re.match("\d+(?:,\d*)*\.*\d*", area):
                    if area[-1] == "_":
                        area = area + "km2"
                    else:
                        area = area + "_km2"
                elif re.match("\d+(?:,\d*)*\.*\d*_km", area):
                    area = area + "2"
            if not re.match("\d+(?:,\d*)*\.*\d*_km2", area):
                return None
        return area
    except Exception as e:
        print(e)
        exit()


def add_country(url, g):
    try:
        country_name = url.split("/")[-1]
        res = requests.get(url)
        doc = lxml.html.fromstring(res.content)
        info_box = doc.xpath("//table[contains(@class, 'infobox')]")[0]
        capital = get_field_capital(info_box, field='Capital', country_name=country_name)

        fields = ['President', ' President', 'president']
        president = None
        president_birth_date = None
        for field in fields:
            president, president_birth_date = get_field_president_prime(info_box, field=field,
                                                                        country_name=country_name)
            if president:
                break

        prime_minister = None
        prime_birth_date = None

        if country_name.lower() != "Brunei".lower():
            fields = ['Prime Minister', ' Prime Minister', 'prime minister', 'Prime minister']
            for field in fields:
                prime_minister, prime_birth_date = get_field_president_prime(info_box, field=field,
                                                                             country_name=country_name)
                if prime_minister:
                    break
        population = get_population(info_box, field='Population', country_name=country_name)
        government = get_field_government(info_box, field='Government')
        area = get_area(info_box, country_name)
        add_ontology(president, "president", country_name, g)
        add_ontology(prime_minister, "prime_minister", country_name, g)
        add_ontology(population, "population", country_name, g)
        add_ontology(area, "area", country_name, g)
        add_ontology(government, "government", country_name, g)
        add_ontology(capital, "capital", country_name, g)
        add_ontology(president_birth_date, "president_born", country_name, g)
        add_ontology(prime_birth_date, "prime_minister_born", country_name, g)
    except Exception as e:
        print(e)
        exit()


def clear_str(text):
    try:
        while "__" in text:
            text = text.replace("__", "_")
        while text.startswith("_"):
            text = text[1:]
        while text.endswith("_"):
            text = text[:-1]
        text = text.strip().lower()
        return text
    except Exception as e:
        print(e)
        exit()


def add_ontology(left, relation, right, g):
    try:
        if left is None:
            left = ""
        if right is None:
            right = ""
        left = clear_str(left)
        right = clear_str(right)
        relation = clear_str(relation)
        left_onto = rdflib.URIRef(wiki_prefix + "/" + left)
        relation = rdflib.URIRef(wiki_prefix + "/" + relation)
        right_onto = rdflib.URIRef(wiki_prefix + "/" + right)
        g.add((left_onto, relation, right_onto))
    except Exception as e:
        print(e)
        exit()


def create():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"
        r = requests.get(url)
        doc = lxml.html.fromstring(r.content)

        # Initialize our knowledge graph object
        g = rdflib.Graph()

        countries_rows = doc.xpath("(//table[@id='main'])/tbody/tr")
        country_links = []
        for row in countries_rows[1:-1]:
            country_link = row.xpath("td")[0].xpath(".//a/@href")
            country_links.append(country_link[0])

        for country_link in country_links:
            add_country(wiki_prefix + country_link, g)

        g.serialize("ontology.nt", format="nt")
        return 0
    except Exception as e:
        print(e)
        exit()


#############################################################################################
#
#                                  Questions and Answers:
#
#############################################################################################

def print_answer(answers_obj, field="x", president=False, prime_minister=False):
    try:
        answers = []
        if len(answers_obj.bindings):
            for bind in answers_obj.bindings:
                answer = bind[field].toPython()
                answer = answer.split(ontology_prefix)[-1]
                answers.append(str(answer).replace("_", " "))
        answer = ", ".join(answers)
        if president:
            print("President of %s" % answer)
        elif prime_minister:
            print("Prime minister of %s" % answer)
        else:
            print(answer)
    except Exception as e:
        print(e)
        exit()


def question_1(list_words, g):
    try:
        country_list = list_words[5:]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "president> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_2(list_words, g):
    try:
        country_list = list_words[6:]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "prime_minister> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_3(list_words, g):
    try:
        country_list = list_words[5:]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "population> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_4(list_words, g):
    try:
        country_list = list_words[5:]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "area> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_5(list_words, g):
    try:
        country_list = list_words[5:]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "government> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_6(list_words, g):
    try:
        country_list = list_words[5:]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "capital> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_7(list_words, g):
    try:
        # ignore the last word (born?)
        country_list = list_words[5:-1]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "president_born> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_8(list_words, g):
    try:
        # ignore the last word (born?)
        country_list = list_words[6:-1]
        country = "_".join(country_list)
        country = country.strip().lower()
        # translate SPARQL question:
        q = "select ?x where { ?x <" + ontology_prefix + "prime_minister_born> <" + ontology_prefix + country + ">}"
        answers = g.query(q)
        print_answer(answers)
    except Exception as e:
        print(e)
        exit()


def question_9(list_words, g):
    try:
        entity_list = list_words[2:]
        entity = "_".join(entity_list)
        entity = entity.strip().lower()
        # translate SPARQL question:
        q = "select ?x where {" \
            " <" + ontology_prefix + entity + "> <" + ontology_prefix + "president> ?x}"
        answers = g.query(q)
        if len(answers):
            print_answer(answers, president=True)
        q = "select ?x where {" \
            " <" + ontology_prefix + entity + "> <" + ontology_prefix + "prime_minister> ?x}"
        answers = g.query(q)
        if len(answers):
            print_answer(answers, prime_minister=True)
    except Exception as e:
        print(e)
        exit()


def check_1_2_9(list_words, g):
    try:
        if list_words[3] == "president":
            question_1(list_words, g)
        elif list_words[3] == "prime" and list_words[4] == "minister":
            question_2(list_words, g)
        else:
            question_9(list_words, g)
    except Exception as e:
        print(e)
        exit()


def check_3_4_5_6(list_words, g):
    try:
        if list_words[3] == "population":
            question_3(list_words, g)
        elif list_words[3] == "area":
            question_4(list_words, g)
        elif list_words[3] == "government":
            question_5(list_words, g)
        else:
            question_6(list_words, g)
    except Exception as e:
        print(e)
        exit()


def check_7_8(list_words, g):
    try:
        if list_words[3] == "president":
            question_7(list_words, g)
        else:
            question_8(list_words, g)
    except Exception as e:
        print(e)
        exit()


def answer_question(question):
    # load ontology file
    g = None
    try:
        nt_file = "ontology.nt"
        g = rdflib.Graph()
        g.parse(nt_file, format="nt")
    except Exception as e:
        print("couldn't load ontology.nt file, use create to create the file")
        print(e)
        exit()
    try:
        question = question.lower().replace("?", "")
        list_words = question.split()
        if list_words[0] == "who":
            check_1_2_9(list_words, g)
        elif list_words[0] == "what":
            check_3_4_5_6(list_words, g)
        elif list_words[0] == "when":
            check_7_8(list_words, g)
    except Exception as e:
        print(e)
        exit()


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: \npython geo_qa.py create ontology.nt\npython geo_qa.py question “<natural language question string>”")
        sys.exit(1)
    try:
        if sys.argv[1] == "create" and sys.argv[2] == "ontology.nt":
            create()
        elif sys.argv[1] == "question":
            answer_question(sys.argv[2].lower())
        else:
            print("Format Error: \nplease try again")
    except Exception as e:
        print("Error: %s\nplease try again" % e.args)


if __name__ == '__main__':
    main()
