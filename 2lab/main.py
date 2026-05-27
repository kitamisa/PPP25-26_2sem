import math
import itertools
import functools
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def polygon_area_calc(vertices):
    n = len(vertices)
    if n < 3:
        return 0.0
    total = 0.0
    for idx in range(n):
        x1, y1 = vertices[idx]
        x2, y2 = vertices[(idx + 1) % n]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0

def polygon_perimeter_calc(vertices):
    n = len(vertices)
    if n < 2:
        return 0.0
    total = 0.0
    for idx in range(n):
        x1, y1 = vertices[idx]
        x2, y2 = vertices[(idx + 1) % n]
        total += math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return total

def point_distance_calc(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def slice_stream(stream, count):
    return list(itertools.islice(stream, count))

def display_polygons(polygons_list, figure_title, axis_handle=None, with_fill=True):
    if axis_handle is None:
        _, axis_handle = plt.subplots(figsize=(8, 6))
    for single_poly in polygons_list:
        if not single_poly:
            continue
        patch_obj = patches.Polygon(
            single_poly, closed=True, edgecolor='darkblue', 
            facecolor='lightblue' if with_fill else 'none',
            alpha=0.7, linewidth=1.5
        )
        axis_handle.add_patch(patch_obj)
    axis_handle.autoscale()
    axis_handle.set_aspect('equal')
    axis_handle.set_title(figure_title)
    axis_handle.grid(True, linestyle='--', alpha=0.3)
    axis_handle.axhline(y=0, color='gray', linewidth=0.5, alpha=0.3)
    axis_handle.axvline(x=0, color='gray', linewidth=0.5, alpha=0.3)
    return axis_handle

def generate_rectangles(width, height, gap=10):
    for position in itertools.count():
        x_start = position * (width + gap)
        yield (
            (x_start, 0),
            (x_start + width, 0),
            (x_start + width, height),
            (x_start, height)
        )

def generate_triangles(side_length, gap=10):
    triangle_height = side_length * math.sqrt(3) / 2
    for position in itertools.count():
        x_start = position * (side_length + gap)
        yield (
            (x_start, 0),
            (x_start + side_length, 0),
            (x_start + side_length/2, triangle_height)
        )

def generate_hexagons(radius, gap=10):
    for position in itertools.count():
        center_x = position * (2 * radius + gap) + radius
        center_y = radius
        vertices = []
        for angle_idx in range(6):
            angle_rad = math.radians(60 * angle_idx)
            vertices.append((
                center_x + radius * math.cos(angle_rad),
                center_y + radius * math.sin(angle_rad)
            ))
        yield tuple(vertices)

def apply_translation(delta_x, delta_y):
    def transformer(polygon_stream):
        return map(lambda poly: tuple((x + delta_x, y + delta_y) for x, y in poly), polygon_stream)
    return transformer

def apply_rotation(angle_degrees, center_point=(0, 0)):
    angle_rad = math.radians(angle_degrees)
    cx, cy = center_point
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    def transformer(polygon_stream):
        return map(
            lambda poly: tuple(
                (
                    cx + (x - cx) * cos_a - (y - cy) * sin_a,
                    cy + (x - cx) * sin_a + (y - cy) * cos_a
                ) for x, y in poly
            ),
            polygon_stream
        )
    return transformer

def apply_mirror(axis='x'):
    if axis == 'x':
        return lambda stream: map(lambda poly: tuple((x, -y) for x, y in poly), stream)
    elif axis == 'y':
        return lambda stream: map(lambda poly: tuple((-x, y) for x, y in poly), stream)
    else:
        cx, cy = axis
        return lambda stream: map(lambda poly: tuple((2*cx - x, 2*cy - y) for x, y in poly), stream)

def apply_scaling(scale_factor, center_point=(0, 0)):
    cx, cy = center_point
    return lambda stream: map(
        lambda poly: tuple(
            (cx + (x - cx) * scale_factor, cy + (y - cy) * scale_factor) 
            for x, y in poly
        ),
        stream
    )

def filter_convex_polygons(stream):
    def is_convex(poly):
        n = len(poly)
        if n < 3:
            return False
        signs = []
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i+1)%n]
            x3, y3 = poly[(i+2)%n]
            cross = (x2-x1)*(y3-y2) - (y2-y1)*(x3-x2)
            if abs(cross) > 1e-10:
                signs.append(1 if cross > 0 else -1)
        return all(s == signs[0] for s in signs) if signs else True
    return filter(is_convex, stream)

def filter_by_angle_at_point(target_point):
    px, py = target_point
    def angle_filter(stream):
        def has_angle_at_point(poly):
            return any(abs(x - px) < 1e-8 and abs(y - py) < 1e-8 for x, y in poly)
        return filter(has_angle_at_point, stream)
    return angle_filter

def filter_by_max_area(max_area):
    def area_filter(stream):
        return filter(lambda poly: polygon_area_calc(poly) < max_area, stream)
    return area_filter

def filter_by_short_side(min_length):
    def short_side_filter(stream):
        def has_short_side(poly):
            poly_list = list(poly)
            n = len(poly_list)
            for i in range(n):
                if point_distance_calc(poly_list[i], poly_list[(i+1)%n]) < min_length:
                    return True
            return False
        return filter(has_short_side, stream)
    return short_side_filter

def filter_containing_point(target_point):
    px, py = target_point
    def point_filter(stream):
        def point_inside_polygon(poly):
            poly_list = list(poly)
            inside = False
            n = len(poly_list)
            for i in range(n):
                x1, y1 = poly_list[i]
                x2, y2 = poly_list[(i-1)%n]
                if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1):
                    inside = not inside
            return inside
        return filter(point_inside_polygon, stream)
    return point_filter

def filter_by_intersecting_polygon(reference_poly):
    ref_list = list(reference_poly)
    def intersect_filter(stream):
        def has_common_vertex(poly):
            poly_list = list(poly)
            for v in poly_list:
                for rv in ref_list:
                    if abs(v[0]-rv[0]) < 1e-8 and abs(v[1]-rv[1]) < 1e-8:
                        return True
            return False
        return filter(has_common_vertex, stream)
    return intersect_filter

def merge_polygon_streams(*streams):
    return map(lambda group: tuple(itertools.chain.from_iterable(group)), zip(*streams))

def count_polygons(stream):
    return sum(1 for _ in stream)

def pair_streams(*streams):
    return map(lambda group: tuple(group), zip(*streams))

def build_transform_decorator(transform_func):
    def decorator(generator_func):
        @functools.wraps(generator_func)
        def wrapped(*args, **kwargs):
            return transform_func(generator_func(*args, **kwargs))
        return wrapped
    return decorator

def build_filter_decorator(filter_func_factory):
    def decorator(generator_func):
        @functools.wraps(generator_func)
        def wrapped(*args, **kwargs):
            stream = generator_func(*args, **kwargs)
            return filter_func_factory(stream)
        return wrapped
    return decorator

def find_closest_to_origin(stream):
    polys = list(stream)
    if not polys:
        return None
    def min_distance_to_origin(poly):
        return min(point_distance_calc(pt, (0, 0)) for pt in poly)
    return functools.reduce(
        lambda best, curr: curr if min_distance_to_origin(curr) < min_distance_to_origin(best) else best,
        polys
    )

def find_max_edge_length(stream):
    def max_edge(poly):
        poly_list = list(poly)
        return max(
            point_distance_calc(poly_list[i], poly_list[(i+1)%len(poly_list)]) 
            for i in range(len(poly_list))
        )
    return functools.reduce(lambda current_max, poly: max(current_max, max_edge(poly)), stream, 0.0)

def find_min_polygon_area(stream):
    return functools.reduce(
        lambda current_min, poly: min(current_min, polygon_area_calc(poly)),
        stream,
        float('inf')
    )

def sum_perimeters(stream):
    return functools.reduce(
        lambda total, poly: total + polygon_perimeter_calc(poly),
        stream,
        0.0
    )

def sum_areas(stream):
    return functools.reduce(
        lambda total, poly: total + polygon_area_calc(poly),
        stream,
        0.0
    )

def main():
    fig1, axes1 = plt.subplots(3, 1, figsize=(15, 16))
    
    display_polygons(slice_stream(generate_triangles(20), 7), "7 Equilateral Triangles", axes1[0])
    display_polygons(slice_stream(generate_rectangles(30, 15), 7), "7 Rectangles", axes1[1])
    display_polygons(slice_stream(generate_hexagons(15), 7), "7 Regular Hexagons", axes1[2])
    fig1.tight_layout()
    
    fig2, axes2 = plt.subplots(3, 2, figsize=(14, 14))
    plt.subplots_adjust(hspace=0.35, wspace=0.3)
    
    def ribbon_rectangles():
        return slice_stream(generate_rectangles(30, 15, 10), 5)
    
    rotated_ribbons = itertools.chain(
        apply_rotation(25)(iter(ribbon_rectangles())),
        apply_rotation(25)(apply_translation(0, 45)(iter(ribbon_rectangles()))),
        apply_rotation(25)(apply_translation(0, 90)(iter(ribbon_rectangles())))
    )
    display_polygons(list(rotated_ribbons), 'Three Parallel Ribbons at 25°', axes2[0, 1], with_fill=True)
    
    def triangle_sequence():
        return slice_stream(generate_triangles(30, 10), 6)
    
    mirrored_triangles = itertools.chain(
        apply_translation(0, 15)(iter(triangle_sequence())),
        apply_translation(0, 110)(apply_mirror('x')(iter(triangle_sequence())))
    )
    display_polygons(list(mirrored_triangles), 'Two Parallel Symmetric Triangle Ribbons', axes2[1, 0], with_fill=True)
    
    def small_rectangles():
        return slice_stream(generate_rectangles(20, 10, 5), 8)
    
    crossed_ribbons = itertools.chain(
        apply_translation(60, 60)(apply_rotation(45, (0,0))(iter(small_rectangles()))),
        apply_translation(60, 60)(apply_rotation(-45, (0,0))(iter(small_rectangles())))
    )
    display_polygons(list(crossed_ribbons), "Crossing Ribbons (intersection not at origin)", axes2[0, 0], with_fill=True)
    
    base_quad = ((10, 5), (35, 8), (30, 25), (8, 22))
    scaled_quads = [next(apply_scaling(0.5 + i*0.4, (0, 0))(iter([base_quad]))) for i in range(8)]
    display_polygons(scaled_quads, "Quadrilaterals at Different Scales", axes2[1, 1], with_fill=False)
    
    fifteen_scaled = [next(apply_scaling(1 + i*0.3, (0, 0))(iter([((0, 0), (25, 0), (25, 25), (0, 25))]))) for i in range(18)]
    short_side_filtered = slice_stream(filter_by_short_side(28)(iter(fifteen_scaled)), 4)
    display_polygons(short_side_filtered, "Filter: side < 28 (4 of 18 selected)", axes2[2, 0], with_fill=True)
    
    @build_transform_decorator(apply_rotation(45, (60, 60)))
    @build_filter_decorator(filter_by_max_area(2500))
    def decorated_polygon_source():
        return generate_rectangles(25, 12, 15)
    
    display_polygons(slice_stream(decorated_polygon_source(), 7), "With decorators (rotation + area filter)", axes2[2, 1], with_fill=True)
    
    plt.show()
    
    print("=" * 60)
    print("AGGREGATION FUNCTIONS (using functools.reduce)")
    print("=" * 60)
    
    test_polys = slice_stream(generate_rectangles(25, 25, 8), 12)
    print(f"Total area of 12 squares: {sum_areas(iter(test_polys)):.2f}")
    
    test_polys2 = slice_stream(generate_rectangles(25, 25, 8), 12)
    print(f"Total perimeter: {sum_perimeters(iter(test_polys2)):.2f}")
    
    test_polys3 = slice_stream(generate_rectangles(25, 25, 8), 12)
    print(f"Maximum edge length: {find_max_edge_length(iter(test_polys3)):.2f}")
    
    test_polys4 = slice_stream(generate_rectangles(25, 25, 8), 12)
    min_a = find_min_polygon_area(iter(test_polys4))
    print(f"Minimum area: {min_a:.2f}")
    
    test_polys5 = slice_stream(generate_rectangles(25, 25, 8), 12)
    nearest = find_closest_to_origin(iter(test_polys5))
    print(f"Polygon closest to origin: {nearest}")
    
    print("\n" + "=" * 60)
    print("ADDITIONAL UTILITIES (count_polygons and pair_streams)")
    print("=" * 60)
    
    tri_seq = list(slice_stream(generate_triangles(20), 5))
    print(f"count_polygons: polygon count = {count_polygons(iter(tri_seq))}")
    
    iter1 = slice_stream(generate_triangles(15), 3)
    iter2 = slice_stream(generate_rectangles(20, 10, 5), 3)
    zipped_pairs = list(pair_streams(iter(iter1), iter(iter2)))
    print(f"pair_streams result (3 pairs):")
    for idx, (tri, rect) in enumerate(zipped_pairs):
        print(f"  Pair {idx+1}: triangle({len(tri)} vertices) + rectangle({len(rect)} vertices)")
    
    print("\n" + "=" * 60)
    print("FUNCTION merge_polygon_streams (polygon stitching)")
    print("=" * 60)
    stream_a = slice_stream(generate_triangles(20), 3)
    stream_b = slice_stream(generate_rectangles(20, 15, 25), 3)
    merged_result = list(merge_polygon_streams(iter(stream_a), iter(stream_b)))
    for idx, poly in enumerate(merged_result):
        print(f"Stitched polygon #{idx+1}: {len(poly)} vertices")

if __name__ == "__main__":
    main()

