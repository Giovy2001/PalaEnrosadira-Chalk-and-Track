"""Condizioni d'uso (pagina statica)."""

from flask import render_template


def render_use_condition():
    return render_template("use_condition.html")
