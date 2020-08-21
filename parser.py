import networkx as nx
import obonet
import os
from collections import defaultdict
import re


def get_synonyms(data):
    """Format synonyms as dicionary
    exact and related synonyms are the keys, and their values are in lists
    """
    if 'synonym' in data:
        syn_dict = {}
        exact = []
        related = []
        broad = []
        for syn in data['synonym']:
            if 'EXACT' in syn:
                match = re.findall(r'\"(.+?)\"', syn)
                exact = exact + match
            elif 'RELATED' in syn:
                match = re.findall(r'\"(.+?)\"', syn)
                related = related + match
            elif 'BROAD' in syn:
                match = re.findall(r'\"(.+?)\"', syn)
                broad = broad + match
        synonyms = {}
        if len(exact) > 0:
            synonyms["exact"] = exact
        if len(related) > 0:
            synonyms["related"] = related
        if len(broad) > 0:
            synonyms["broad"] = broad
        return synonyms
    else:
        return {}


def load_data(data_folder):
    url = "http://purl.obolibrary.org/obo/mp.obo"
    graph = obonet.read_obo(url)
    for item in graph.nodes():
        rec = graph.nodes[item]
        rec["_id"] = item
        rec["mp"] = item
        if rec.get("is_a"):
            rec["parents"] = [parent for parent in rec.pop(
                "is_a") if parent.startswith("MP:")]
        if rec.get("xref"):
            xrefs = defaultdict(set)
            for val in rec.get("xref"):
                if ":" in val:
                    prefix, id = val.split(':', 1)
                    if prefix in ["http", "https"]:
                        continue
                    if prefix.lower() in ['umls', 'snomedct_us', 'snomed_ct', 'cohd', 'ncit']:
                        xrefs[prefix.lower()].add(id)
                    elif prefix == 'MSH':
                        xrefs['mesh'].add(id)
                    else:
                        xrefs[prefix.lower()].add(val)
            for k, v in xrefs.items():
                xrefs[k] = list(v)
            rec.pop("xref")
            rec["xrefs"] = dict(xrefs)
        rec["children"] = [child for child in graph.predecessors(
            item) if child.startswith("MP:")]
        rec["ancestors"] = [ancestor for ancestor in nx.descendants(
            graph, item) if ancestor.startswith("MP:")]
        rec["descendants"] = [descendant for descendant in nx.ancestors(
            graph, item) if descendant.startswith("MP:")]
        rec["synonym"] = get_synonyms(rec)
        if rec.get("created_by"):
            rec.pop("created_by")
        if rec.get("creation_date"):
            rec.pop("creation_date")
        if rec.get("relationship"):
            for rel in rec.get("relationship"):
                predicate, val = rel.split(' ')
                prefix = val.split(':')[0]
                rec[predicate] = {prefix.lower(): val}
            rec.pop("relationship")
        yield rec
