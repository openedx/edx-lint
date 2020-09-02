"""
Checks for unsafe @@TODO
"""
from pylint.checkers import BaseChecker
from pylint.interfaces import IAstroidChecker

from .common import BASE_ID, check_visitors



def register_checkers(linter):
    """Register checkers."""
    linter.register_checker(CrossMonolithImportChecker(linter))


@check_visitors
class CrossMonolithImportChecker(BaseChecker):
    """
    Checks for @@TODO
    """

    __implements__ = (IAstroidChecker,)

    name = "cross-monolith-import-checker"

    MESSAGES = {
        (importer, importee): {
            "code": "E{:2}{:2}".format(BASE_ID, code_number)
            "id": "importing-{}-within-{}".format(importer, importee),
            "message": "Importing from `{}/` while inside a `{}/` module.".format(
                importee, importer
            ),
        }
        for code_number, importer, importee
        in [
            (81, "lms", "cms"),  # In LMS, do not import Studio code.
            (82, "cms", "lms"),  # In Studio, do not import LMS code.
            (83, "openedx", "lms"),  # In openedx (shared), do not import LMS code.
            (84, "openedx", "cms"),  # In openedx (shared), do not import Studio code.
            (84, "common", "lms"),  # In common (shared), do not import LMS code.
            (84, "common", "cms"),  # In common (shared), do not import Studio code.
        ]
    }

    @staticmethod
    def is_node_within_lms(node):
        """
        Check whether a node is within the `lms/` top-level directory.

        Due to the PYTHONPATH-modification hack in edx-platform/lms/envs/common.py,
        LMS modules can go by both fully-qualified (`lms.djangoapps.$app.$module`)
        and partially-qualified (`$app.$module`) names, making it difficult to tell
        via regular means whether an AST node is within the LMS top-level folder.
        So, instead, we check using the actual file path of the module.

        This shares most of its logic with `is_node_within_cms`, but they are separate,
        in anticipation of the directory structures of LMS/Studio developing
        indepenently of one another.

        Arguments:
            node (NodeNG)

        Returns: bool
        """
        module_fpath = node.root().file or ""
        # We could just check for "/lms/", but that is more likely to return
        # false-positives, as it possible that some other edX repository has an
        # `lms` sub-package.
        # Also, we could just check for "/edx-platform/lms/", but that assumes that
        # the repository is checked out into `edx-platform`.
        # So, match on the three subdirectores of `lms/` that contain Python code.
        # We knowlingly exclude modules in the `lms/` directory itself.
        if "/lms/djangoapps/" in module_fpath:
            return True
        if "/lms/lib/" in module_fpath:
            return True
        if "/lms/envs/" in module_fpath:
            return True
        return False


    @staticmethod
    def is_node_within_cms(node):
        """
        @@TODO
        """
        # @@TODO
        return False

    def validate_import(self, node): 

    def visit_import(self, node):
        """
        @@TODO
        """
        for name, _ in node.names or []:
            if self.is_node_within_lms(node):



    # @@TODO
    '''
    msgs = {
        "C{}57".format(BASE_ID): (
            u"yaml.load%s() call is unsafe, use yaml.safe_load%s()",
            MESSAGE_ID,
            "yaml.load*() is unsafe",
        )
    }

    @utils.check_messages(MESSAGE_ID)
    def visit_call(self, node):
        """
        Check whether a call is an unsafe call to yaml.load.
        """
        func_name = node.func.as_string()
        if func_name in self.UNSAFE_CALLS:
            suffix = func_name.lstrip("yaml.load")
            self.add_message(self.MESSAGE_ID, args=(suffix, suffix), node=node)
    '''