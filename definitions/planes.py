from models.plane import Plane

planes = {
    'a0': Plane(plane_id='a0',
                name='Plane 1',
                cost=200,
                speed=1,
                weight=1,
                capacity_type='P',
                capacity=1,
                flight_range=1,
                size_class=1),

    'a1': Plane(plane_id='a1',
                name='Plane 2',
                cost=200,
                speed=1,
                weight=1,
                capacity_type='C',
                capacity=1,
                flight_range=1,
                size_class=1)
}
