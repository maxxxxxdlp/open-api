
# .............................................................................
class S2nService:
    """
    Base S-to-the-N service, handles parameter names and value types
    """
    # ...............................................
    def _fix_type(self, usr_val, default_val):
        # all strings are lower case
        try:
            usr_val = usr_val.lower()
        except:
            pass
        # Test membership in value options
        if isinstance(default_val, list):
            if usr_val not in default_val:
                usr_val = None
        elif isinstance(default_val, tuple):
            if len(default_val) == 2 and None in default_val:
                ex_val = default_val[0]
                if ex_val is None:
                    ex_val = default_val[1]
                if not isinstance(usr_val, type(ex_val)):
                    usr_val = None
            else:
                usr_val = None
        # Convert int, str to boolean
        elif isinstance(default_val, bool):                
            if usr_val in (0, '0', 'no', 'false'):
                return False
            else:
                return True
        elif isinstance(default_val, str):                
            usr_val = str(usr_val)
        # Values that cannot be converted correctly are changed to default value
        elif isinstance(default_val, float):
            try:             
                usr_val = float(usr_val)
            except:
                usr_val = default_val
        elif isinstance(default_val, int):                
            try:             
                usr_val = int(usr_val)
            except:
                usr_val = default_val
        return usr_val

    # ...............................................
    def _get_def_val(self, default_val):
        # Default val in value options is first
        if isinstance(default_val, list):
            def_val = default_val[0]
        elif isinstance(default_val, tuple):
            def_val = None
        else:
            def_val = default_val
        return def_val

        
    # ...............................................
    def _process_params(self, kwarg_defaults, user_kwargs):
        """
        Modify all user provided key/value pairs to change keys to lower case, 
        and change values to the expected type (string, int, float, boolean).
        
        Args:
            kwarg_defaults: dictionary of 
                * keys containing valid keyword parameters for the current 
                    service. All must be lowercase.
                * values containing 
                    * the default value or 
                    * list of valid values (first is default), or
                    * tuple of 2 elements: None (default), and a value of the correct type 
            user_kwargs: dictionary of keywords and values sent by the user for 
                the current service.
                
        Note:
            A list of valid values for a keyword can include None as a default 
                if user-provided value is invalid
        """
        good_params = {}
        # Correct all parameter keys/values present
        for key, val in user_kwargs.items():
            key = key.lower()
            try:
                ptype = kwarg_defaults[key]
            except:
                pass
            else:
                val = self._fix_type(val, ptype)
                good_params[key] = val
        # Add missing defaults
        for dkey, dval in kwarg_defaults.items():
            try:
                good_params[dkey]
            except:
                good_params[dkey] = self._get_def_val(dval)
        return good_params

# .............................................................................
if __name__ == '__main__':
    kwarg_defaults = {
        'count_only': False,
        'width': 600,
        'height': 300,
        'type': [],
        }