#!/usr/bin/env python3

import pint
from math import pi
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from collections import OrderedDict

ureg = pint.UnitRegistry()
ureg.define('revolution = 6.2831853 * radian = rev')

# tool properties (for 3/4" 4 flute endmill)
tool_diameter = 0.75 * ureg.inch
tooth_count = 4 * (1 / ureg.rev)

tools = [
    {
        'diameter': 3/4 * ureg.inch,
        'tooth_count': 4 * (1 / ureg.rev),
        'material': 'hss',
    },
    {
        'diameter': 3/8 * ureg.inch,
        'tooth_count': 2 * (1 / ureg.rev),
        'material': 'carbide',
    },
    {
        'diameter': 3/16 * ureg.inch,
        'tooth_count': 2 * (1 / ureg.rev),
        'material': 'carbide',
    },
]

materials = OrderedDict([
    ('Aluminum', {
        'SFM': 300 * (ureg.ft / ureg.min),
        'unit_power': 0.4 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('Mild Steel', {
        'SFM': 100 * (ureg.ft / ureg.min),
        'unit_power': 1.8 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('4130 Steel', {
        'SFM': 80 * (ureg.ft / ureg.min),
        'unit_power': 2.2 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('4140 Steel, annealed', {
        'SFM': 60 * (ureg.ft / ureg.min),
        'unit_power': 2.2 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
    ('4140 Steel, hardened', {
        'SFM': 30 * (ureg.ft / ureg.min),
        'unit_power': 2.6 * (ureg.hp / (ureg.inch**3 / ureg.min)),
    }),
])

# machine properties
horsepower_motor = 0.5 * ureg.hp
machine_efficiency = 0.75  # dimensionless fraction

for tool in tools:
    # X axis values
    doc_axial = np.arange(0.0, tool_diameter.to(ureg.inch).magnitude + 0.01, 0.01) * ureg.inch
    
    fig, ax = plt.subplots()
    
    for material_name, material_properties in materials.items():
        RPM = material_properties['SFM'] / ( pi * tool_diameter / ureg.rev )
        IPM = 0.005 * tool_diameter * RPM * tooth_count
        MRR = horsepower_motor * machine_efficiency / material_properties['unit_power']
        doc_radial = MRR / IPM / doc_axial
        stepover = 100 * (doc_radial / tool_diameter).to(ureg.dimensionless)
    
        ax.plot(doc_axial, stepover, label='{}: {:.0f} RPM, {:.1f} IPM'.format(
            material_name,
            RPM.to(ureg.rev / ureg.min).magnitude,
            IPM.to(ureg.inch / ureg.min).magnitude,
            ))
    
    ax.legend()
    
    ax.set(xlabel='DOC, Axial (inch)', ylabel='Stepover (percent)',
           title='Milling Parameters, {:.2f} hp, {:.2f}" {:d} fl HSS End Mill'.format(
               horsepower_motor.magnitude,
               tool_diameter.magnitude,
               int(tooth_count.magnitude),
               ))
    ax.set_xlim(0, tool_diameter.to(ureg.inch).magnitude)
    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, step=5))
    ax.grid()
    
    plt.show()
