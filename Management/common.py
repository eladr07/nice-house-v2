from datetime import datetime, date
from django.core.exceptions import ObjectDoesNotExist

import reversion

from NiceHouse.settings import BASE_DIR

LAWYER_TAX = 1.015

def get_year_choices():
    today = date.today()
    return ((i,i) for i in range(today.year - 10, today.year + 10))

def get_month_choices():
    return ((i,i) for i in range(1,13))

def current_month():
    now = datetime.now()
    if now.day <= 22:
        now = datetime(now.month == 1 and now.year - 1 or now.year, 
                       now.month == 1 and 12 or now.month - 1, 
                       now.day)
    return now

def generate_unique_media_filename(ext):
    import os
    filename = datetime.now().strftime('%Y%m%d%H%M%S') + '.' + ext
    full_path = os.path.join(BASE_DIR, 'temp', filename)
    return full_path

def clone(from_object, save):
    args = dict([(fld.name, getattr(from_object, fld.name)) 
                 for fld in from_object._meta.fields 
                 if fld is not from_object._meta.pk])
    if save:
        return from_object.__class__.objects.create(**args)
    else:
        new_object = from_object.__class__(**args)
        return new_object
    
def restore_object(instance, date):
    from reversion.models import Version

    # get all versions of the given instance
    instance_versions = Version.objects.get_for_object(obj=instance)

    # filter by data in RevisionExt object
    versions = instance_versions.filter(revision__revisionext__date__lte = date)

    if versions.count() > 0:
        version = versions.latest('revision__revisionext__date')
    else:
        try:
            # filter by date_created in Revision object
            version = instance_versions.filter(revision__date_created__lte=date).latest('revision__date_created')
        except ObjectDoesNotExist:
            return instance
    return version.object

#def has_versions(obj, additional_fields = None):
#    # go over the commission model and its childs to find out if it has a versions (history of changes)
#    Version = reversion.models.Version
#    
#    has_versions = False
#    obj_versions = Version.objects.get_for_object(obj)
#    
#    # every models has at leasy 1 version
#    if len(obj_versions) > 1:
#        has_versions = True
#    # if we haven't found a version on the model itself, we go over 'additional_fields' if exist
#    elif additional_fields:
#        additional_fields_metas = [field for field in obj._meta.fields if field.name in additional_fields]
#        for field_meta in additional_fields_metas:
#            if has_versions:
#                break
#            
#            if not field_meta.rel:
#                continue
#            
#            # get the actual field valud on 'obj'
#            field_val = getattr(obj, field.name)
#            
#            if not field.rel.multiple:
#                # recursively run this function on the field
#                has_versions = has_versions(field_val)
#            else:
#                for field_val_item in field_val.all():
#                    if has_versions:
#                        break
#                    has_versions = has_versions(field_val_item)                        
#        
#    return has_versions