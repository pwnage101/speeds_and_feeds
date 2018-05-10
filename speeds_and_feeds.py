#!/usr/bin/env python3

import pint
from math import pi
import matplotlib
matplotlib.use('PDF')
import matplotlib.pyplot as plt
import numpy as np
from collections import OrderedDict
from fractions import Fraction


ureg = pint.UnitRegistry()
ureg.define('revolution = 6.2831853 * radian = rev')

MAX_DOC_AXIAL = 1.3  # multiple of tool diameter

tools = [
    {
        'diameter': 3/4 * ureg.inch,
        'tooth_count': 4 * (1 / ureg.rev),
        'material': 'hss',
    },
    {
        'diameter': 3/8 * ureg.inch,
        'tooth_count': 2 * (1 / ureg.rev),
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
    doc_axial = np.arange(0.0, MAX_DOC_AXIAL * tool['diameter'].to(ureg.inch).magnitude + 0.01, 0.01) * ureg.inch
    
    fig, ax = plt.subplots()
    
    for material_name, material_properties in materials.items():
        SFM = material_properties['SFM']
        if tool['material'] is 'carbide':
            SFM *= 2.0
        RPM = SFM / ( pi * tool['diameter'] / ureg.rev )
        IPM = 0.005 * tool['diameter'] * RPM * tool['tooth_count']
        MRR = horsepower_motor * machine_efficiency / material_properties['unit_power']
        doc_radial = MRR / IPM / doc_axial
        stepover = 100 * (doc_radial / tool['diameter']).to(ureg.dimensionless)
    
        ax.plot(doc_axial, stepover, label='{}: {:.0f} RPM, {:.1f} IPM'.format(
            material_name,
            RPM.to(ureg.rev / ureg.min).magnitude,
            IPM.to(ureg.inch / ureg.min).magnitude,
            ))
    
    ax.legend()
    
    ax.set(xlabel='DOC, Axial (inch)', ylabel='Stepover (percent)',
           title='Milling Parameters, {:.2f} hp, {}" {:d} fl {} End Mill'.format(
               horsepower_motor.magnitude,
               Fraction(tool['diameter'].magnitude).limit_denominator(),
               int(tool['tooth_count'].magnitude),
               tool['material'],
               ))
    ax.set_xlim(0, MAX_DOC_AXIAL * tool['diameter'].to(ureg.inch).magnitude)
    ax.set_ylim(0, 100)
    ax.set_yticks(np.arange(0, 101, step=5))
    ax.grid()

    ax2 = ax.twinx()
    ax2.set_ylim(0, tool['diameter'].magnitude)
    yticks = np.arange(0, tool['diameter'].magnitude*1.05, step=tool['diameter'].magnitude*0.05)
    ax2.set_yticks(yticks)
    ax2.set_yticklabels(['{:.3f}" [{:.2f}]'.format(tick, (tick * ureg.inch).to(ureg.mm).magnitude) for tick in yticks])
    ax2.set_ylabel('Stepover (inch/mm)')

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    
    fig.savefig("speeds_and_feeds_{:.2f}hp_{:.3f}in_{:d}fl_{}_endmill.pdf".format(
        horsepower_motor.magnitude,
        tool['diameter'].magnitude,
        int(tool['tooth_count'].magnitude),
        tool['material'],
        ))
    #plt.show()
