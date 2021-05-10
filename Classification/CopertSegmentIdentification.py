def segment_identification_for_each_category(row) -> str:
    """
    Function that identifies the Segment type of each vehicle given it's Category, Fuel, weight and engine.

    :param row: row of a pd.DataFrame that contains itv register data
    :return: Segment type
    """
    # Segment classification of Passenger Cars Category
    if row['Category'] == 'Passenger Cars':

        if row['Fuel'] == 'Petrol':
            if row['CC_CM3'] < 800:
                return 'Mini'
            if 800 <= row['CC_CM3'] < 1400:
                return 'Small'
            if 1400 <= row['CC_CM3'] <= 2000:
                return 'Medium'
            if row['CC_CM3'] > 2000:
                return 'Large-SUV-Executive'
            else:
                print('Petrol Passenger Cars with no Segment associated')
                print(row)
                print('-')
                return None

        elif row['Fuel'] == 'Diesel' or row['Fuel'] == 'Petrol Hybrid' or row['Fuel'] == 'Diesel Hybrid':   # Diesel Mini specifications not found ???
            if row['CC_CM3'] < 1400:
                return 'Small'
            if 1400 <= row['CC_CM3'] <= 2000:
                return 'Medium'
            if row['CC_CM3'] > 2000:
                return 'Large-SUV-Executive'
            else:
                print('Diesel Passenger Cars with no Segment associated')
                print(row)
                print('-')
                return None

        elif row['Fuel'] == 'Battery electric' or row['Fuel'] == 'Petrol PHEV' or row['Fuel'] == 'Diesel PHEV':
            return 'Medium'  # NO he trobat a cap lloc com diferencia el Segment per cotxes electrics i híbrids

        else:
            print('Passenger Cars with no Segment associated')
            print(row)
            print('-')

    # Segment classification of Light Commercial Vehicles
    elif row['Category'] == 'Light Commercial Vehicles':
        if row['PES_BUIT'] <= 1305:
            return 'N1-I'
        elif 1305 < row['PES_BUIT'] <= 1760:
            return 'N1-II'
        elif 1760 < row['PES_BUIT'] <= 3500:
            return 'N1-III'
        elif row['PES_BUIT'] > 3500:
            print('Light Commercial vehicle over max weigth of 3500kg, must be recategorized to Heavy Duty Truck:')
            print(row)
            print('-')
            return None

    # Segment classification of Heavy Duty Trucks
    elif row['Category'] == 'Heavy Duty Trucks':   # Articulated trucks cannot be diferenciated with the available data
        if 3500 <= row['PES_BUIT'] <= 7500:
            return 'Rigid <=7,5 t'
        elif 7500 < row['PES_BUIT'] < 12000:
            return 'Rigid 7,5 - 12 t'
        elif 12000 <= row['PES_BUIT'] < 14000:
            return 'Rigid 12 - 14 t'
        elif 14000 <= row['PES_BUIT'] < 20000:
            return 'Rigid 14 - 20 t'
        elif 20000 <= row['PES_BUIT'] < 26000:
            return 'Rigid 20 - 26 t'
        elif 26000 <= row['PES_BUIT'] < 28000:
            return 'Rigid 26 - 28 t'
        elif 28000 <= row['PES_BUIT'] <= 32000:
            return 'Rigid 28 - 32 t'
        elif row['PES_BUIT'] > 32000:
            return 'Rigid >32 t '
        else:
            print('Truck with no Segment associated:')
            print(row)
            print('-')
            return None

    # Segment classification for Buses
    elif row['Category'] == 'Buses':     # Articulated buses not taken into account, cannot be differenciated with data
        if row['Fuel'] == 'Diesel':
            if row['PES_BUIT'] <= 15000:
                return 'Urban Buses Midi <=15 t'
            elif 15000 < row['PES_BUIT'] <= 18000:
                return 'Urban Buses Standard 15 - 18 t'
            elif row['PES_BUIT'] > 18000:
                return 'Urban Buses Articulated >18 t'
            else:
                print('Bus with no Segment associated:')
                print(row)
                print('-')
                return None
        elif row['Fuel'] == 'CNG':
            return 'Urban CNG Buses'
        elif row['Fuel'] == 'Biodiesel':
            return 'Urban Biodiesel Buses'
        elif row['Fuel'] == 'Diesel Hybrid':
            return 'Urban Buses Diesel Hybrid'
        else:
            print('Bus with no Segment associated')
            print(row)
            print('-')

    # Segment classification for Motorcycles
    elif row['Category'] == 'L-Category':
        if row['CC_CM3'] <= 50:  # Mopeds & Motorcycles of 2 & 4 strokes cannot be differenciated with available data
            return 'Mopeds 2-stroke <50 cm³'
        elif row['CC_CM3'] < 250:
            return 'Motorcycles 4-stroke <250 cm³'
        elif 250 <= row['CC_CM3'] <= 750:
            return 'Motorcycles 4-stroke 250 - 750 cm³'
        elif row['CC_CM3'] > 750:
            return 'Motorcycles 4-stroke >750 cm³'
        else:
            print('L-Category with no Segment associated:')  # Quad & ATVs and Micro-car not taken into account
            print(row)
            print('-')
            return None

    else:
        print('Vehicle with no Category')
        print(row)
        print('-')