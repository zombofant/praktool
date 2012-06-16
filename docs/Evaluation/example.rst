**Example:** Measuring the density of a cube
============================================

Let's examine the following experiment. We have a cube of material of
which we do not know what it is. It's a perfect cube so that we can
just measure one edge and know its volume. We can also measure the
weight using a scale.

.. highlight:: python

First the following pre-setup, assuming that praktool is in your
pythonpath::

>>> from Evaluation.Table import Table
>>> from Evaluation.Column import MeasurementColumn
>>> import sympy.physics.units as units

Now let's assume we did some measurements for our cube. To be sure to
avoid measurement errors, we did multiple measurements for both the
mass *m* and the edge length *a*:

====== ======
a / cm m / kg
====== ======
1.007  0.0962 
0.001  0.0968
0.995  0.114 
0.994  0.0876
0.999  0.115 
====== ======

So now we want to mangle that data in python using praktool.

>>>

... to be continued ...
