# -*- coding: utf-8 -*-

#Script based on GEWISS_buildings_v1.5 assigning

import arcpy
import re

fc =  arcpy.GetParameterAsText(0) #'D:\HiwiGEWISS\BUE_Test\Sample_for_script_testing.gdb\Altona'
uuid_f = arcpy.GetParameterAsText(1)
build_func_f =  arcpy.GetParameterAsText(2) #"GFK"
baujahr_f =  arcpy.GetParameterAsText(3) #"BJA"
bauweise_f =  arcpy.GetParameterAsText(4) #"BAW"
an_og_f =  arcpy.GetParameterAsText(5) #"AOG"
dachform_f =  arcpy.GetParameterAsText(6) #"DAF"
grundfl_f = arcpy.GetParameterAsText(7) #GRF
kennwerte_xls = arcpy.GetParameterAsText(8)
ext_daten_xls = arcpy.GetParameterAsText(9)

def xls_to_dict(file_path, fields):
    xls = file_path + '\Sheet1$'
    rows = arcpy.SearchCursor(xls)

    d = {}
    for row in rows:
        d[row.getValue(fields[0])] = {field : row.getValue(field) for field in fields[1:]}

    return d

def clean_baujahr(baujahr):
    cleaned =  re.findall(r'\d+', str(baujahr))
    integ = [int(cl) for cl in cleaned if int(cl) > 10]
    if len(integ) == 0:
       orig_changed = (0,0)
    else:
        orig = min(integ)
        changed = max(integ)
        if orig in [1500,1600,1700,1800]: #dummy variables 
            orig_changed = (0, changed)
        else:
            orig_changed = (orig, changed)
    return orig_changed #a tuple as in (0,0) or (1920,1960)

def constr_year_epoch(dt_baujahr, alkis_bj):
    if dt_baujahr != 0:
        cleaned = dt_baujahr
    else:
        cleaned = clean_baujahr(alkis_bj)[0]

    if cleaned == 0:
        epoch = "_"
    elif cleaned > 2040:
        epoch = "_"
    elif cleaned <= 1859:
        epoch = "A"
    elif 1860 <= cleaned <= 1918:
        epoch = "B"
    elif 1919 <= cleaned <= 1948:
        epoch = "C"
    elif 1949 <= cleaned <= 1957:
        epoch = "D"
    elif 1958 <= cleaned <= 1968:
        epoch = "E"
    elif 1969 <= cleaned <= 1978:
        epoch = "F"
    elif 1979 <= cleaned <= 1983:
        epoch = "G"
    elif 1984 <= cleaned <= 1994:
        epoch = "H"
    elif 1995 <= cleaned <= 2001:
        epoch = "I"
    elif 2002 <= cleaned <= 2009:
        epoch = "J"
    elif 2010 <= cleaned <= 2015:
        epoch = "K"
    elif cleaned >= 2016:
        epoch = "L"

    return epoch

def assign_iwu(gfk_klasse, bauweise, anOG, epoch):
    bautyp = "_"
    #--------------------------------------------------------------------------
    if "wohnen" not in gfk_klasse:
        return "_" #CHANGED 
    #--------------------------------------------------------------------------
    elif epoch == "A":
        if bauweise in [1100, 2200, 2100] and anOG <= 2:
            bautyp = "EFH"
        elif bauweise in [1200, 2300, 2400, 2500]: 
            bautyp = "MFH"
        else:
            if anOG <= 2:
                bautyp = "EFH"
            else:
                bautyp = "MFH"
    #--------------------------------------------------------------------------
    elif epoch in ["B", "C", "D"]:
        if bauweise == 1100 and anOG <= 2:
            bautyp = "EFH"
        elif bauweise in [2200, 2100] and anOG <= 2:
            bautyp = "RH"
        elif bauweise in [1200, 2300, 2400, 2500]:
            if anOG <= 4:
                bautyp = "MFH"
            elif anOG >= 5:
                bautyp = "GMH"
        else:
            if anOG <= 2:
                bautyp = "EFH"
            elif 3 <= anOG <= 4:
                bautyp = "MFH"
            elif anOG >= 5:
                bautyp = "GMH"
    #--------------------------------------------------------------------------
    elif epoch in ["E", "F"]:
        if bauweise == 1100 and anOG <= 2:
            bautyp = "EFH"
        elif bauweise in [2200, 2100] and anOG <= 2:
            bautyp = "RH"
        elif bauweise in [1200, 2300, 2400, 2500]:
            if anOG <= 5:
                bautyp = "MFH"
            elif 6 <= anOG <= 8:
                bautyp = "GMH"
            elif anOG > 8:
                bautyp = "HH"
        else:
            if anOG <= 2:
                bautyp = "EFH"
            elif 3 <= anOG <= 5:
                bautyp = "MFH"
            elif 6 <= anOG <= 8:
                bautyp = "GMH"
            elif anOG > 8:
                bautyp = "HH"
    #--------------------------------------------------------------------------
    elif epoch in ["G","H","I","J","K","L"]:
        if bauweise == 1100 and anOG <= 2:
            bautyp = "EFH"
        if bauweise in [2200, 2100] and anOG <= 2:
            bautyp = "RH"
        elif bauweise in [1200, 2300, 2400, 2500]: 
            bautyp = "MFH"
        else:
            if anOG <= 2:
                bautyp = "EFH"
            else:
                bautyp = "MFH"
    #--------------------------------------------------------------------------
    elif epoch == '_':
        if bauweise == 1100 and anOG <= 2:
            bautyp = "EFH"
        elif bauweise in [2200, 2100] and anOG <= 2:
            bautyp = "RH"
        elif bauweise in [1200, 2300, 2400, 2500]:
            if anOG <= 5:
                bautyp = "MFH"
            elif 6 <= anOG <= 8:
                bautyp = "GMH"
            elif anOG > 8:
                bautyp = "HH"
        else:
            if anOG <= 2:
                bautyp = "EFH"
            elif 3 <= anOG <= 5:
                bautyp = "MFH"
            elif 6 <= anOG <= 8:
                bautyp = "GMH"
            elif anOG > 8:
                bautyp = "HH"
    return "%s_%s" % (bautyp,epoch)

def nutzfl_EnEV_func(an_og, dachform, grundfl, gfk_klasse, iwu_typ): 
    
    roof_type_list = [
        #1000, #Flachdach 
        #2100, #Pultdach 
        #2200, #Versetztes Pultdach 
        3100, #Satteldach 
        3200, #Walmdach 
        3300, #Krüppelwalmdach 
        3400 #Mansardendach 
        #3500, #Zeltdach 
        #3600, #Kegeldach 
        #3700, #Kuppeldach 
        #3800, #Sheddach 
        #3900, #Bogendach 
        #4000, #Turmdach 
        #5000, #Mischform 
        #9999 #Sonstiges 
        ]
    
    heated_roofs_iwu_list = ["EFH_A","EFH_B","EFH_C",
	                         "EFH_D","EFH_E","RH_B",
                             "RH_C","RH_D","RH_E","MFH_A"]

    flaecheEnEv = 0
    
    if "wohnen" in gfk_klasse:
        #Mansardendach and Krüppelwalmdach counted always as heated
        if dachform in [3300,3400]:
            flaecheEnEv = grundfl * (an_og + 0.75)
		#if heated according to iwu
        elif dachform in roof_type_list and iwu_typ in heated_roofs_iwu_list:
            flaecheEnEv = grundfl * (an_og + 0.75)
		#general case
        else:
            flaecheEnEv = grundfl * an_og

    elif gfk_klasse in ["gewerbe", "oeffentlich", "gewerbe_oeffentlich", "sonder"]:
        flaecheEnEv = grundfl * an_og
 
    return flaecheEnEv

def spez_flaeche(nutzfl_EnEV, iwu_typ, gfk_klasse, grundfl, an_og):

    wohnfl = 0
    nwg_fl = 0
	
    if gfk_klasse == "wohnen_gemischt_0.85":
        nutzfl_EnEV_wohn = nutzfl_EnEV * 0.15
        nwg_fl = nutzfl_EnEV * 0.85
    elif gfk_klasse == "wohnen_gemischt_0.5":
        nutzfl_EnEV_wohn = nutzfl_EnEV * 0.5
        nwg_fl = nutzfl_EnEV * 0.5
    elif gfk_klasse == "wohnen_gemischt_erdg" and an_og == 1:
        nutzfl_EnEV_wohn = nutzfl_EnEV * 0.5
        nwg_fl = nutzfl_EnEV * 0.5
    elif gfk_klasse == "wohnen_gemischt_erdg":
        nutzfl_EnEV_wohn = nutzfl_EnEV-grundfl
        nwg_fl = grundfl
    elif gfk_klasse == "wohnen":
        nutzfl_EnEV_wohn = nutzfl_EnEV

    else: #gewerbe, oeffentlich, sonder
        nwg_fl = nutzfl_EnEV
    
    if "EFH" in iwu_typ:
        wohnfl = nutzfl_EnEV_wohn * 0.77
    elif "RH" in iwu_typ:
        wohnfl = nutzfl_EnEV_wohn * 0.81
    elif "MFH" in iwu_typ:
        wohnfl = nutzfl_EnEV_wohn * 0.80
    elif "GMH" in iwu_typ:
        wohnfl = nutzfl_EnEV_wohn * 0.80
    elif "HH" in iwu_typ:
        wohnfl = nutzfl_EnEV_wohn * 0.80

    return int(wohnfl), int(nwg_fl)


#read xls
kennwerte_dict = xls_to_dict(kennwerte_xls, ["Code", "ALKIS_Name", "GFK_Klasse", "VDI_Name", "HEWW_m2_UNSAN", "HEWW_m2_SAN1"])

#Check for external Table
if ext_daten_xls and ext_daten_xls != '#':
	ext_data_field_spec = [
				"UUID", "Ext_Daten", "GFK_Klasse", "Energietraeger", "IWU_Typ", "NWG_Typ", "Nutzfl_EnEV", "wohnfl", "nwg_fl", 
				"Wohn_HEWW_m2_UNSAN", "NWG_HEWW_m2_UNSAN", "HEWW_total_UNSAN", "Wohn_HEWW_m2_SAN1",
				"NWG_HEWW_m2_RW", "HEWW_total_SAN1_RW", "HEWW_total_Wohn_UNSAN", "HEWW_total_Wohn_SAN1",
				"HEWW_total_NWG_UNSAN", "HEWW_total_NWG_RW"
				]
	ext_data_dict = xls_to_dict(ext_daten_xls, ext_data_field_spec)
else:
    ext_data_dict = {}


# Execute AddField
arcpy.AddField_management(fc, "Ext_Daten", "STRING")
arcpy.AddField_management(fc, "GFK_Klasse", "STRING")
arcpy.AddField_management(fc, "Energietraeger", "STRING")
arcpy.AddField_management(fc, "IWU_Typ", "STRING")
arcpy.AddField_management(fc, "NWG_Typ", "STRING")
arcpy.AddField_management(fc, "Nutzfl_EnEV", "Integer")
arcpy.AddField_management(fc, "wohnfl", "Integer")
arcpy.AddField_management(fc, "nwg_fl", "Integer")

arcpy.AddField_management(fc, "Wohn_HEWW_m2_UNSAN", "Double")
arcpy.AddField_management(fc, "NWG_HEWW_m2_UNSAN", "Double")
arcpy.AddField_management(fc, "HEWW_total_UNSAN", "Integer")

arcpy.AddField_management(fc, "Wohn_HEWW_m2_SAN1", "Double")
arcpy.AddField_management(fc, "NWG_HEWW_m2_RW", "Double") #Richtwert
arcpy.AddField_management(fc, "HEWW_total_SAN1_RW", "Integer")

arcpy.AddField_management(fc, "HEWW_total_Wohn_UNSAN", "Integer")
arcpy.AddField_management(fc, "HEWW_total_Wohn_SAN1", "Integer")
arcpy.AddField_management(fc, "HEWW_total_NWG_UNSAN", "Integer")
arcpy.AddField_management(fc, "HEWW_total_NWG_RW", "Integer")

fields = (
    baujahr_f,
    build_func_f,
    bauweise_f, 
    an_og_f,
    dachform_f,
    grundfl_f,
    "SHAPE@",
    uuid_f,
    "Ext_Daten",
	"GFK_Klasse",
	"Energietraeger",
    "IWU_Typ",
    "NWG_Typ",
    "Nutzfl_EnEV",
    "wohnfl",
    "nwg_fl",

    "Wohn_HEWW_m2_UNSAN",
    "NWG_HEWW_m2_UNSAN",
    "HEWW_total_UNSAN",
    "Wohn_HEWW_m2_SAN1",
    "NWG_HEWW_m2_RW",
    "HEWW_total_SAN1_RW",
	
    "HEWW_total_Wohn_UNSAN",
    "HEWW_total_Wohn_SAN1",
    "HEWW_total_NWG_UNSAN",
    "HEWW_total_NWG_RW"
    )

with arcpy.da.UpdateCursor(fc, fields) as cursor:

    for row in cursor:
        baujahr = row[0]
        build_func = row[1]
        bauweise = row[2]
        an_og = row[3]
        dachform = row[4]
        grundfl = row[5]
        geom = row[6]
        uuid = row[7]
        
        #Check if the inputs are valid
        #baujahr uses a re search, any input is ok
        #bauweise can be any, it is checked for values
        if not an_og or not grundfl or not build_func:
            row[8] = "k.A."
            row[9] = "GFK/AOG/GRF fehlt oder 0"
            row[10] = "k.A."
            row[11] = "k.A."
            row[12] = "k.A."
            for i in range(13,26):
                row[i] = 0
            cursor.updateRow(row)
        #geom is not checked
        #uuid is only used for looking up in an external table, so a None is tolerable


        #Check external sources
        elif uuid in ext_data_dict.keys():
            for i, v in zip(range(8,27), ext_data_field_spec[1:]):
                row[i] = ext_data_dict[uuid][v]

            cursor.updateRow(row)


        else:
			epoch = constr_year_epoch(0, baujahr)
			gfk_klasse = kennwerte_dict.get(str(build_func), {"GFK_Klasse" : "unbekannte Nutzung"})["GFK_Klasse"]
			iwu_typ = assign_iwu(gfk_klasse, bauweise, an_og, epoch)
			nwg_typ = kennwerte_dict.get(str(build_func), {"VDI_Name" : "_"})["VDI_Name"]
			nutzfl_EV = nutzfl_EnEV_func(an_og, dachform, grundfl, gfk_klasse, iwu_typ)
			flaechen = spez_flaeche(nutzfl_EV, iwu_typ, gfk_klasse, grundfl, an_og)
			wohnfl = flaechen[0]
			nwg_fl = flaechen[1]
			wohn_bedarf_UNSAN = kennwerte_dict.get(iwu_typ, {"HEWW_m2_UNSAN" : 0})["HEWW_m2_UNSAN"]
			nwg_bedarf_UNSAN = kennwerte_dict.get(str(build_func), {"HEWW_m2_UNSAN" : 0})["HEWW_m2_UNSAN"]
			wohn_bedarf_san1 = kennwerte_dict.get(iwu_typ, {"HEWW_m2_SAN1" : 0})["HEWW_m2_SAN1"]
			nwg_bedarf_richtwert = kennwerte_dict.get(str(build_func), {"HEWW_m2_SAN1" : 0})["HEWW_m2_SAN1"]

			row[8] = "k.A."
			row[9] = gfk_klasse
			row[10] = "k.A."
			row[11] = iwu_typ
			row[12] = nwg_typ
			row[13] = nutzfl_EV
			row[14] = wohnfl
			row[15] = nwg_fl

			row[16] = wohn_bedarf_UNSAN
			row[17] = nwg_bedarf_UNSAN
			row[18] = (wohnfl*wohn_bedarf_UNSAN) + (nwg_fl*nwg_bedarf_UNSAN)

			row[19] = wohn_bedarf_san1
			row[20] = nwg_bedarf_richtwert
			row[21] = (wohnfl*wohn_bedarf_san1) + (nwg_fl*nwg_bedarf_richtwert)
			
			row[22] = wohnfl*wohn_bedarf_UNSAN #In order to be able to sum all the demands for residential use in residential and mixed-use buildings
			row[23] = wohnfl*wohn_bedarf_san1
			row[24] = nwg_fl*nwg_bedarf_UNSAN
			row[25] = nwg_fl*nwg_bedarf_richtwert
			
			cursor.updateRow(row)