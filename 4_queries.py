import rdflib
from rdflib import Literal
import sys
from rdflib import Literal, XSD

wiki_prefix = r"http://en.wikipedia.org/"


def main():
    g = None
    nt_file = "ontology.nt"
    try:
        g = rdflib.Graph()
        g.parse(nt_file, format="nt")
    except Exception as e:
        print(e)
        exit()

    prime_minister_count_res = g.query('select (count(DISTINCT ?p) as ?counter) where {\
                                        ?p <http://en.wikipedia.org/prime_minister> ?c .\
                                        FILTER(str(?p)!="http://en.wikipedia.org/")}')
    prime_minister_count = prime_minister_count_res.bindings[0]["counter"].toPython()

    countries_count_res = g.query('select (count(DISTINCT ?c) as ?counter) where {\
                                        ?a <http://en.wikipedia.org/area> ?c .\
                                        FILTER(str(?c)!="http://en.wikipedia.org/")}')
    countries_count = countries_count_res.bindings[0]["counter"].toPython()

    republic_count_res = g.query('select (count(DISTINCT ?c) as ?counter) where {\
                                  ?g <http://en.wikipedia.org/government> ?c .\
                                  FILTER regex(str(?g),"republic")}')
    republic_count = republic_count_res.bindings[0]["counter"].toPython()

    monarchy_count_res = g.query('select (count(DISTINCT ?c) as ?counter) where {\
                                  ?g <http://en.wikipedia.org/government> ?c .\
                                  FILTER regex(str(?g),"monarchy")}')
    monarchy_count = monarchy_count_res.bindings[0]["counter"].toPython()

    with open("2_results.txt", "w", encoding="utf-8") as f:
        f.write("prime minister count: %s\n" % prime_minister_count)
        f.write("countries count: %s\n" % countries_count)
        f.write("republic count: %s\n" % republic_count)
        f.write("monarchy count: %s\n" % monarchy_count)


if __name__ == "__main__":
    main()
