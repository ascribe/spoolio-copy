def merge_acl_dict_with_object(acl_dict, acl_obj, startswith='acl_'):
    """
    override acl_dict with acl_obj in the AND-sense
    the 'value and getattr(acl_obj, attr)' sets the acl to False if they are not allowed

    :param acl_dict: dictionary {acl_* : bool}
    :param acl_obj: object with attributes acl_* = bool
    :return: dict : keys: of acl_dict,
                    values: overridden with acl_obj "FALSE" if value is an attribute of acl_obj
    """
    return {attr: (value and getattr(acl_obj, attr)
                   if hasattr(acl_obj, attr)
                   else value)
            for attr, value in acl_dict.iteritems()
            if attr.startswith(startswith)}


def merge_acl_dicts(acl_dict_1, acl_dict_2, startswith='acl_'):
    """
    override acl_dict with acl_obj in the AND-sense
    the 'value and getattr(acl_obj, attr)' sets the acl to False if they are not allowed

    :param acl_dict_1: dictionary {acl_* : bool}
    :param acl_dict_2: dictionary {acl_* : bool}
    :return: dict : keys: of acl_dict_1,
                    values: overridden with acl_dict_2 "FALSE" if value is a key of acl_dict_2
    """
    return {attr: (value and acl_dict_2.get(attr, value))
            for attr, value in acl_dict_1.iteritems()
            if attr.startswith(startswith)}
