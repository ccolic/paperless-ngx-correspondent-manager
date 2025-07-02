"""Paperless-ngx Correspondent Manager

A CLI utility to manage paperless-ngx correspondents.
"""

__version__ = "1.0.1"
__author__ = "Christian Colic"
__email__ = "christian@colic.io"

from .manager import PaperlessCorrespondentManager

__all__ = ["PaperlessCorrespondentManager"]
