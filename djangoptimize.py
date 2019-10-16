""" Searches for optimizable django queries """

import ast
import sys
from pprint import pprint

class Analyzer(ast.NodeVisitor):
    """ Analises multiple querysets nester 
        Example:
            BAD:
                users = UserWithOID.objects.filter(id__in=chunk)
                user_profiles = UserProfile.objects.filter(user__in=users)
                licenses = License.objects.filter(userprofile__in=user_profiles)
            GOOD:
                licenses = License.objects.filter(userprofile__user_id__chunk)

        BAD:
        SELECT "management_license"."id", "management_license"."bought_by", "management_license"."valid_from", "management_license"."valid_until", "management_license"."type", "management_license"."created_presentations", "management_license"."downloaded_presentations", "management_license"."first_desktop_login", "management_license"."trial_until", "management_license"."license_type_oid", "management_license"."userprofile_id", "management_license"."product_name" FROM "management_license" WHERE ("management_license"."userprofile_id" IN (SELECT V0."id" FROM "management_userprofile" V0 WHERE V0."user_id" IN (SELECT U0."id" FROM "auth_user" U0 WHERE U0."id" IN (91, 92, 93, 94, 95, 96, 97, 98, 99, 100))) AND "management_license"."license_type_oid" IN (pitchsulairvideoprivacy0y0e))
        GOOD:
    """
    def __init__(self):
        self.stats = {"call": [], "names": []}

    def visit_Call(self, node):
        """ collects where __in=... is called """
        for kw in node.keywords:
            if '__in' in kw.arg:
                if hasattr(kw.value, 'id'):
                    self.stats['call'].append('{}: {}.objects.filter(...={})'.format(
                        node.lineno,
                        node.func.value.value.id,
                        kw.value.id))
                    self.stats["names"].append(kw.value.id)
        self.generic_visit(node)

    def report(self):
        na = NamesAnalizer(self.stats["names"])
        na.visit(tree)
        na.report()
        pprint(self.stats)

class NamesAnalizer(ast.NodeVisitor):
    def __init__(self, names):
        self.names = names
        self.stats = {"findings": []}

    def visit_Assign(self, node):
        try:
            for t in node.targets:
                if hasattr(t, 'id') and t.id in self.names:
                    for kw in node.value.keywords:
                        if '__in' in kw.arg:
                            self.stats['findings'].append(
                                '{}: {}=...'.format(
                                node.lineno,
                                t.id)
                            )
        except:
            import ipdb;ipdb.set_trace()

    def report(self):
        pprint(self.stats)

    

# TODO: parse args better with argparse or something
f = open(sys.argv[1])
tree = ast.parse(f.read())

analyzer = Analyzer()
analyzer.visit(tree)
analyzer.report()

