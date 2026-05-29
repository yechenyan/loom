from __future__ import annotations


TUTORIAL_FILES = {
    "loom.md": "source: github.com/pysa\n",
    "costs_2040-modifications.csv": """technology,parameter,value,unit,source,further description
gas,fuel,22.6,EUR/MWh_th,Ariadne,
oil,fuel,38.3564,EUR2020/MWh,Ariadne,"$2020 = 0.8775 EUR2020, 1bbl = 1.6998MWh"
coal,fuel,6.3036,EUR2020/MWh,Ariadne,"$2020 = 0.8775 EUR2020, 1t = 8.06 MWh"
OCGT,investment,696,EUR2020/kW,DEA,
electricity distribution grid,investment,1500,EUR2020/kW,oriented towards JRC-EU-TIMES
HVAC overhead,investment,472,EUR2020/MW/km,NEP2021,"Assuming High Temperature Low Sag Cables with higher Amperage"
HVAC overhead,investment,772,EUR2020/MW/km,NEP2023,"Assuming High Temperature Low Sag Cables with higher Amperage"
offwind-ac-connection-submarine,investment,3786,EUR2020/MW/km,NEP2021,"220kv, 1A, 2 circuits, 3 phases, inflation"
offwind-ac-connection-submarine,investment,2488,EUR2020/MW/km,NEP2023,
offwind-ac-station,investment,697,EUR2020/kW,NEP2021,"cost of two stations, landseitig and seeseitig"
offwind-ac-station,investment,722,EUR2020/kW,NEP2023,"cost of two stations, landseitig and seeseitig"
HVDC inverter pair,investment,597015,EUR2020/MW,NEP2021+NEP2023
HVDC overhead,investment,995,EUR2020/MW/km,NEP2021+NEP2023
HVDC underground,investment,3234,EUR2020/MW/km,NEP2021,
HVDC underground,investment,2978,EUR2020/MW/km,NEP2023,
""",
    "costs_2045-modifications.csv": """technology,parameter,value,unit,source,further description
gas,fuel,22.8,EUR/MWh_th,Ariadne,
oil,fuel,38.0983,EUR2020/MWh,Ariadne,"$2020 = 0.8775 EUR2020, 1bbl = 1.6998MWh"
coal,fuel,6.3472,EUR2020/MWh,Ariadne,"$2020 = 0.8775 EUR2020, 1t = 8.06 MWh"
OCGT,investment,684,EUR2020/kW,DEA,
electricity distribution grid,investment,1500,EUR2020/kW,oriented towards JRC-EU-TIMES
HVAC overhead,investment,472,EUR2020/MW/km,NEP2021,"Assuming High Temperature Low Sag Cables with higher Amperage"
HVAC overhead,investment,772,EUR2020/MW/km,NEP2023,"Assuming High Temperature Low Sag Cables with higher Amperage"
offwind-ac-connection-submarine,investment,3786,EUR2020/MW/km,NEP2021,"220kv, 1A, 2 circuits, 3 phases, inflation"
offwind-ac-connection-submarine,investment,2488,EUR2020/MW/km,NEP2023,
offwind-ac-station,investment,697,EUR2020/kW,NEP2021,"cost of two stations, landseitig and seeseitig"
offwind-ac-station,investment,722,EUR2020/kW,NEP2023,"cost of two stations, landseitig and seeseitig"
HVDC inverter pair,investment,597015,EUR2020/MW,NEP2021+NEP2023
HVDC overhead,investment,995,EUR2020/MW/km,NEP2021+NEP2023
HVDC underground,investment,3234,EUR2020/MW/km,NEP2021,
HVDC underground,investment,2978,EUR2020/MW/km,NEP2023,
""",
    "costs_2050-modifications.csv": """technology,parameter,value,unit,source,further description
gas,fuel,22.9,EUR/MWh_th,Ariadne,
oil,fuel,37.8918,EUR2020/MWh,Ariadne,"$2020 = 0.8775 EUR2020, 1bbl = 1.6998MWh"
coal,fuel,6.4016,EUR2020/MWh,Ariadne,"$2020 = 0.8775 EUR2020, 1t = 8.06 MWh"
OCGT,investment,671,EUR2020/kW,DEA,
electricity distribution grid,investment,1500,EUR2020/kW,oriented towards JRC-EU-TIMES
HVAC overhead,investment,472,EUR2020/MW/km,NEP2021,"Assuming High Temperature Low Sag Cables with higher Amperage"
HVAC overhead,investment,772,EUR2020/MW/km,NEP2023,"Assuming High Temperature Low Sag Cables with higher Amperage"
offwind-ac-connection-submarine,investment,3786,EUR2020/MW/km,NEP2021,"220kv, 1A, 2 circuits, 3 phases, inflation"
offwind-ac-connection-submarine,investment,2488,EUR2020/MW/km,NEP2023,
offwind-ac-station,investment,697,EUR2020/kW,NEP2021,"cost of two stations, landseitig and seeseitig"
offwind-ac-station,investment,722,EUR2020/kW,NEP2023,"cost of two stations, landseitig and seeseitig"
HVDC inverter pair,investment,597015,EUR2020/MW,NEP2021+NEP2023
HVDC overhead,investment,995,EUR2020/MW/km,NEP2021+NEP2023
HVDC underground,investment,3234,EUR2020/MW/km,NEP2021,
HVDC underground,investment,2978,EUR2020/MW/km,NEP2023,
""",
}
