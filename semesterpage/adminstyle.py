def set_admin_theme():
    """
    Custom styling of the admin site using the admin_interface app.
    Done by editing the default Theme model created by the app at initialization.
    Is invoked by the AppConfig.ready() method.
    """
    from admin_interface.models import Theme
    
    # Getting the default theme
    kokekunster_theme = Theme.objects.get_or_create(pk=1)[0]

    if kokekunster_theme.name != 'Kokekunster':
        # Used colors
        white = '#FFFFFF'
        dark_grey = '#555555'
        darker_grey = '#333333'
        grey = '#7A7A7A'
        bright_grey = '#C0C0C0' # silver
        red = '#BA2121'
        dark_red = '#A41515'

        # Editing the theme
        kokekunster_theme.name = 'Kokekunster'

        kokekunster_theme.title = _('Komfyren')

        kokekunster_theme.logo = '/static/img/kokekunster_logo.svg'

        kokekunster_theme.css_header_background_color = darker_grey
        kokekunster_theme.css_header_title_color = white
        kokekunster_theme.css_header_text_color = bright_grey
        kokekunster_theme.css_header_link_color = white
        kokekunster_theme.css_header_link_hover_color = bright_grey

        kokekunster_theme.css_module_background_color = grey
        kokekunster_theme.css_module_text_color = white
        kokekunster_theme.css_module_link_color = white
        kokekunster_theme.css_module_link_hover_color = bright_grey
        kokekunster_theme.css_module_rounded_corners = False

        kokekunster_theme.css_generic_link_color = dark_grey
        kokekunster_theme.css_generic_link_hover_color = bright_grey

        kokekunster_theme.css_save_button_background_color = dark_grey
        kokekunster_theme.css_save_button_background_hover_color = grey
        kokekunster_theme.css_save_button_text_color = white

        kokekunster_theme.css_delete_button_background_color = red
        kokekunster_theme.css_delete_button_background_hover_color = dark_red
        kokekunster_theme.css_delete_button_text_color = white

        kokekunster_theme.css = '#branding h1 span {' \
                                        'font-size: 30px;' \
                                        'position: relative; ' \
                                        'top: 0.5em; ' \
                                        'font-weight: 300;' \
                                '}' \
                                '.login #branding h1 span {' \
                                        'position: absolute;' \
                                        'right: 2.8em;' \
                                        'top: 1.5em;' \
                                '}' \



        # Done with the changes, thus writing the changes to the database
        kokekunster_theme.save()