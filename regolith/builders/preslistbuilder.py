"""Builder for Lists of Presentations.

This builder will build a presentation list for each group-member in each group
listed in groups.yml.  Group members are indicated in the employment and
education sections of the individual in people.yml.

There are a number of filtering options, i.e., for presentation-type (invited,
colloquium, seminar, poster, contributed_oral) and for whether the invitation
was accepted or declined.  As of now, these filters can only be updated by
editing this file but may appear as command-line options later.  It will also
get institution and department information from institutions.yml if they are
there.

The author list is built from information in people.yml where possible.  The
does a fuzzy search for the person in people.yml but if the person is absent
from people, it will still build but using the string name given in
the presentations.yml.

The presentations are output in a ./_build directory."""

from copy import deepcopy, copy
import datetime, sys

from regolith.builders.basebuilder import LatexBuilderBase
from regolith.fsclient import _id_key
from regolith.sorters import position_key
from regolith.tools import (
    all_docs_from_collection,
    fuzzy_retrieval,
    get_person_contact,
    number_suffix,
    group_member_ids, latex_safe, filter_presentations
)
from regolith.stylers import sentencecase, month_fullnames
from regolith.dates import month_to_int, get_dates

class PresListBuilder(LatexBuilderBase):
    """Build list of talks and posters (presentations) from database entries"""

    btype = "preslist"
    needed_dbs = ['groups', 'institutions', 'people', 'grants',
                  'presentations', 'contacts']


    def construct_global_ctx(self):
        """Constructs the global context"""
        super().construct_global_ctx()
        gtx = self.gtx
        rc = self.rc
        gtx["people"] = sorted(
            all_docs_from_collection(rc.client, "people"),
            key=position_key,
            reverse=True,
        )
        gtx["contacts"] = sorted(
            all_docs_from_collection(rc.client, "contacts"),
            key=position_key,
            reverse=True,
        )
        gtx["grants"] = sorted(
            all_docs_from_collection(rc.client, "grants"), key=_id_key
        )
        gtx["groups"] = sorted(
            all_docs_from_collection(rc.client, "groups"), key=_id_key
        )
        gtx["presentations"] = sorted(
            all_docs_from_collection(rc.client, "presentations"), key=_id_key
        )
        gtx["institutions"] = sorted(
            all_docs_from_collection(rc.client, "institutions"), key=_id_key
        )
        gtx["all_docs_from_collection"] = all_docs_from_collection
        gtx["float"] = float
        gtx["str"] = str
        gtx["zip"] = zip

    def latex(self):
        """Render latex template"""
        everybody = self.gtx["people"] + self.gtx["contacts"]
        for group in self.gtx["groups"]:
            grp = group["_id"]
            grpmember_ids = group_member_ids(self.gtx['people'], grp)
            for member in grpmember_ids:
                if self.rc.people:
                    if member not in self.rc.people:
                        continue
                presclean = filter_presentations(everybody,
                                                 self.gtx["presentations"],
                                                 self.gtx["institutions"],
                                                 member,
                                                 statuses=["accepted"])
#                 types = ["all"]
#                 #                types = ['invited']
#                 #statuses = ["all"]
#                 statuses = ['accepted']
# 
#                 firstclean = list()
#                 secondclean = list()
#                 presclean = list()
# 
#                 # build the filtered collection
#                 # only list the talk if the group member is an author
#                 for pres in presentations:
#                     pauthors = pres["authors"]
#                     if isinstance(pauthors, str):
#                         pauthors = [pauthors]
#                     authors = [
#                         fuzzy_retrieval(
#                             self.gtx["people"],
#                             ["aka", "name", "_id"],
#                             author,
#                             case_sensitive=False,
#                         )
#                         for author in pauthors
#                     ]
#                     authorids = [
#                         author["_id"]
#                         for author in authors
#                         if author is not None
#                     ]
#                     if member in authorids:
#                         firstclean.append(pres)
#                 # only list the presentation if it is accepted
#                 for pres in firstclean:
#                     if pres["status"] in statuses or "all" in statuses:
#                         secondclean.append(pres)
#                 # only list the presentation if it is invited
#                 for pres in secondclean:
#                     if pres["type"] in types or "all" in types:
#                         presclean.append(pres)
# 
#                 # build author list
#                 for pres in presclean:
#                     pauthors = pres["authors"]
#                     if isinstance(pauthors, str):
#                         pauthors = [pauthors]
#                     pres["authors"] = [
#                         author
#                         if not get_person_contact(author, self.gtx["people"],
#                                           self.gtx["contacts"])
#                         else
#                         get_person_contact(author, self.gtx["people"],
#                                    self.gtx["contacts"])["name"]
#                         for author in pauthors
#                     ]
#                     authorlist = ", ".join(pres["authors"])
#                     pres["authors"] = authorlist
#                     presdates = get_dates(pres)
#                     pres["date"] = presdates.get("begin_date")
# #                    all_date_objects = ['day', 'month', 'year']
#                     beg_end = ['begin', 'end']
#                     for be in beg_end:
#                         if presdates.get(f"{be}_date"):
#                             pres[f"{be}_day"] = presdates.get(f"{be}_date").day
#                             pres[f"{be}_month"] = presdates.get(f"{be}_date").month
#                             pres[f"{be}_year"] = presdates.get(f"{be}_date").year
# 
#                     for day in ["begin_day", "end_day"]:
#                         pres["{}_suffix".format(day)] = number_suffix(
#                             pres.get(day, None)
#                         )
#                     if "institution" in pres:
#                         inst = pres["institution"]
#                         try:
#                             pres["institution"] = fuzzy_retrieval(
#                                 self.gtx["institutions"],
#                                 ["aka", "name", "_id"],
#                                 pres["institution"],
#                                 case_sensitive=False,
#                             )
#                             if pres["institution"] is None:
#                                 print(
#                                     "WARNING: institution {} in {} not found in "
#                                     "institutions.yml.  Preslist will build "
#                                     "but to avoid errors please add and "
#                                     "rerun".format(inst, pres["_id"])
#                                 )
#                                 pres["institution"] = {"_id": inst,
#                                                        "department": {
#                                                            "name": ""}}
#                         except:
#                              print("no institute {} in institutions collection".format(inst))
#                              pres["institution"] = {"_id": inst, "department": {"name": ""}}
# #                            sys.exit(
# #                                "ERROR: institution {} not found in "
# #                                "institutions.yml.  Please add and "
# #                                "rerun".format(pres["institution"])
# #                            )
#                         if "department" in pres:
#                             try:
#                                 pres["department"] = pres["institution"][
#                                     "departments"
#                                 ][pres["department"]]
#                             except:
#                                 print(
#                                     "WARNING: department {} not found in"
#                                     " {} in institutions.yml.  Pres list will"
#                                     " build but please check this entry carefully and"
#                                     " please add the dept to the institution!".format(
#                                         pres["department"],
#                                         pres["institution"]["_id"],
#                                     )
#                                 )
#                         else:
#                             pres["department"] = {"name": ""}

                if len(presclean) > 0:
                    presclean = sorted(
                        presclean,
                        key=lambda k: k.get("date", None),
                        reverse=True,
                    )
                    outfile = "presentations-" + grp + "-" + member
                    pi = [
                        person
                        for person in self.gtx["people"]
                        if person["_id"] is member
                    ][0]
                    self.render(
                        "preslist.tex",
                        outfile + ".tex",
                        pi=pi,
                        presentations=presclean,
                        sentencecase=sentencecase,
                        monthstyle=month_fullnames,
                    )
                    self.env.trim_blocks = True
                    self.env.lstrip_blocks = True
                    self.render(
                        "preslist.txt",
                        outfile + ".txt",
                        pi=pi,
                        presentations=presclean,
                        sentencecase=sentencecase,
                        monthstyle=month_fullnames,
                    )
                    self.pdf(outfile)
