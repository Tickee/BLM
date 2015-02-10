from sqlalchemy.sql.expression import func
from sqlalchemy.sql.functions import coalesce
from models import TextLocalisation
import sqlahelper

Session = sqlahelper.get_session()

def create_text_localisation(reference_id=None, text="", lang="en"):
    """
    Creates a new TextLocalisation object. If no reference id supplied, it will create a new reference id.
    """
    if reference_id is None:
        # create new reference
        reference_id = Session.query(coalesce(func.max(TextLocalisation.reference_id), 0)).first()[0] + 1
    
    tl = TextLocalisation(text, lang, reference_id)
    Session.add(tl)
    return tl

def set_translation(reference_id, text, lang="en"):
    """
    Sets the translation of a resource. If a new TextLocalisation object
    had to be created, it will be returned. 
    """
    # find translation object responsible
    translation = get_translation_object(reference_id, lang)
    # adjust it if exists
    if translation:
        translation.text = text
    # create new translation object if not already exists
    else:
        create_text_localisation(reference_id, text, lang)

def get_translation(reference_id, language="en"):
    """
    Returns the translation string.
    """
    # find translation object responsible
    translation = get_translation_object(reference_id, language)
    # return translation if found
    if translation:
        return translation.text
    # return empty string if no translation exists
    else:
        return ""

def get_translation_object(reference_id, language="en"):
    """
    Returns the TextLocalisation object for a specific resource and language.
    """
    return get_translations(reference_id).filter(TextLocalisation.lang==language).first()

    
def get_translations(reference_id):
    return Session.query(TextLocalisation).filter(TextLocalisation.reference_id==reference_id)