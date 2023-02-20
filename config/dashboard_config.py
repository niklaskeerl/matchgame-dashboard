from pygal import Config
from pygal.style import Style


def get_config():
    """
    :return: DashboardConfig object
    """
    return DashboardConfig()


class DashboardConfig:
    """
    Dashboard config that consists of shared configurations for charts
    """
    max_timer_millis = 90000
    correct_style = Style(colors=('#000078', '#585858'))
    table_style = Style(colors=('#490d00', '#8a034f'))

    no_legend_config = Config()
    no_legend_config.show_legend = False
    server_url = "http://localhost:5000"
    fallback_game_config = {
        "http://ddigames.inf.tu-dresden.de/matching-games/inf-eva/": {
            "regEx": {
                "level0": [
                    ['Eingabe', 'Verarbeitung', 'Verarbeitung', 'Eingabe']
                ],
                "level1": [
                    ['Speicherung', 'Ausgabe', 'Ausgabe', 'Speicherung']
                ]
            },
            "words": {
                "level0": [{"matching": ['controller', 'mouse2', 'mouse', 'keyboard', 'keyboard2', 'joystick', 'remote',
                                         'scanner', 'mic', 'webcam', 'webcam2', 'floppy_disc', 'flippy_disc', 'sd_card',
                                         'sd_card2', 'usb2', 'harddrivedisc', 'cd', 'usb', 'external_storage'],
                            "nonMatching": ['sound_system', 'sound_system2', 'headset', 'headphones', 'printer',
                                            'printer2',
                                            'beamer', 'monitor', 'monitor2', 'motherboard', 'motherboard2',
                                            'graphiccard',
                                            'graphiccard2', 'microcontroller', 'cpu', 'cpu2', 'ram']
                            }],
                "level1": [{
                    "matching": ['sound_system', 'sound_system2', 'headset', 'headphones', 'printer', 'printer2',
                                 'beamer',
                                 'monitor', 'monitor2', 'motherboard', 'motherboard2', 'graphiccard', 'graphiccard2',
                                 'microcontroller', 'cpu', 'cpu2', 'ram'],
                    "nonMatching": ['controller', 'mouse2', 'mouse', 'keyboard', 'keyboard2', 'joystick', 'remote',
                                    'scanner', 'mic', 'webcam', 'webcam2', 'floppy_disc', 'flippy_disc', 'sd_card',
                                    'sd_card2', 'usb2', 'harddrivedisc', 'cd', 'usb', 'external_storage']
                }]
            },
            "solution": [{
                "pattern": 'Eingabe',
                "words": ['controller', 'mouse2', 'mouse', 'keyboard', 'keyboard2', 'joystick', 'remote', 'scanner',
                          'mic',
                          'webcam', 'webcam2']
            }, {
                "pattern": 'Ausgabe',
                "words": ['sound_system', 'sound_system2', 'headset', 'headphones', 'printer', 'printer2', 'beamer',
                          'monitor', 'monitor2']
            }, {
                "pattern": 'Verarbeitung',
                "words": ['motherboard', 'motherboard2', 'graphiccard', 'graphiccard2', 'microcontroller', 'cpu',
                          'cpu2',
                          'ram']
            }, {
                "pattern": 'Speicherung',
                "words": ['floppy_disc', 'flippy_disc', 'sd_card', 'sd_card2', 'usb2', 'harddrivedisc', 'cd', 'usb',
                          'external_storage']
            }]
        },
        "http://ddigames.inf.tu-dresden.de/matching-games/inf-ai-process/": {
            "regEx": {
                "level0": [
                    ['Daten sammeln', 'Trainieren', 'Testen', 'Anwenden']
                ]
            },
            "words": {
                "level0": [{
                    "matching": ['unterschiedliche Daten sammeln', 'umso mehr Daten desto besser', 'Modelerstellung',
                                 'Epochen', 'Mustererkennung', 'Trainingsdaten', 'Modelprüfung', 'Testdaten',
                                 'menschliches Eingreifen', 'Zuordnungen können falsch sein', 'Bilderkennung'],
                    "nonMatching": ['gleiche Daten sammeln', 'wenig Daten nötig', 'Emotionen', 'Gehirn']
                }]
            },
            "solution": [{
                "pattern": 'Daten sammeln',
                "words": ['unterschiedliche Daten sammeln', 'umso mehr Daten desto besser', 'menschliches Eingreifen']
            }, {
                "pattern": 'Trainieren',
                "words": ['Modelerstellung', 'Epochen', 'Mustererkennung', 'Trainingsdaten']
            }, {
                "pattern": 'Testen',
                "words": ['Modelprüfung', 'Testdaten', 'menschliches Eingreifen']
            }, {
                "pattern": 'Anwenden',
                "words": ['Zuordnungen können falsch sein', 'Bilderkennung']
            }]
        },
        "http://ddigames.inf.tu-dresden.de/matching-games/inf-ai-systems/": {
            "regEx": {
                "level0": [
                    ['KI', 'Keine KI', 'Keine KI', 'KI']
                ]
            },
            "words": {
                "level0": [{
                    "matching": ['Waschmaschine', 'Rasenmaehroboter', 'Staubsaugerroboter', 'Chatbot', 'Autonomes_Auto',
                                 'Bilderkennung', 'Spracherkennung', 'Humanoide_Roboter', 'Boston_Dynamic_Hund',
                                 'Marsroboter', 'Industrieroboter', 'Toaster', 'Kuehlschrank', 'Wasserkocher',
                                 'Ferngesteuertes_Auto', 'Fahrstuhl'],
                    "nonMatching": []
                }]
            },
            "solution": [{
                "pattern": 'KI',
                "words": ['Rasenmaehroboter', 'Staubsaugerroboter', 'Humanoide_Roboter', 'Boston_Dynamic_Hund',
                          'Marsroboter', 'Autonomes_Auto', 'Bilderkennung', 'Spracherkennung', 'Chatbot',
                          'Industrieroboter']
            }, {
                "pattern": 'Keine KI',
                "words": ['Waschmaschine', 'Rasenmaehroboter', 'Staubsaugerroboter', 'Industrieroboter', 'Toaster',
                          'Kuehlschrank', 'Wasserkocher', 'Ferngesteuertes_Auto', 'Fahrstuhl']
            }]
        }
    }
