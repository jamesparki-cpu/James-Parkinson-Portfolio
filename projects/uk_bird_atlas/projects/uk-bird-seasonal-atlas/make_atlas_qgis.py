"""
Builds the seasonal bird atlas in QGIS from the smoothed surfaces made by smooth_surfaces.py:
one landscape A4 page per species, 12 monthly maps (Jan-Jun on top, Jul-Dec below),
a colour-bar legend in the title band (clear of the maps), title and data credit.
Exports a PNG and a PDF per species to <BASE>/atlas/.

Before running
  1. python smooth_surfaces.py   (writes output/surfaces/*.tif)
  2. Set BASE below to the folder that contains output/ and ne_10m_admin_0_countries.shp
Run
  QGIS > Plugins > Python Console > Show Editor > open this file > Run.
  Re-running is safe; the layout "Bird atlas" stays in the project for manual tweaks.
"""
import os

from qgis.core import (
    Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
    QgsRectangle, QgsSingleSymbolRenderer, QgsFillSymbol, QgsColorRampShader,
    QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsBilinearRasterResampler,
    QgsPrintLayout, QgsLayoutItemPage, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemShape, QgsLayoutPoint, QgsLayoutSize, QgsLayoutExporter,
    QgsTextFormat, QgsUnitTypes,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont

# ------------------------------------------------------------------ settings
BASE = os.path.expanduser("~/uk-bird-seasonal-atlas")   # <-- folder that contains output/
SURFACES = os.path.join(BASE, "output", "surfaces")
COAST_PATH = os.path.join(BASE, "ne_10m_admin_0_countries.shp")
COAST_FILTER = "\"ADMIN\" = 'United Kingdom'"
CITATION = os.path.join(BASE, "output", "gbif_citation.txt")
OUT = os.path.join(BASE, "atlas")
LAYOUT_NAME = "Bird atlas"
GROUP_NAME = "Bird atlas layers"
SIGMA_KM = 8                                      # keep in sync with smooth_surfaces.py

SPECIES = [  # (common name, scientific name, pattern)
    ("Swift", "Apus apus", "summer visitor"),
    ("Swallow", "Hirundo rustica", "summer visitor"),
    ("House Martin", "Delichon urbicum", "summer visitor"),
    ("Cuckoo", "Cuculus canorus", "summer visitor"),
    ("Willow Warbler", "Phylloscopus trochilus", "summer visitor"),
    ("Wheatear", "Oenanthe oenanthe", "passage migrant and upland breeder"),
    ("Redwing", "Turdus iliacus", "winter visitor"),
    ("Fieldfare", "Turdus pilaris", "winter visitor"),
    ("Pink-footed Goose", "Anser brachyrhynchus", "winter visitor"),
    ("Whooper Swan", "Cygnus cygnus", "winter visitor"),
    ("Robin", "Erithacus rubecula", "resident - included as an effort control"),
]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Colour ramp: value stops are roughly doubling, colours are spaced evenly on the bar,
# so low rates (swans, ~2-5%) and high rates (Swallow, ~50%) are both readable.
STOPS = [0, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50]
COLOURS = ["#f3efe2", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#0c2c84"]
TICKS = ["0", "2%", "5%", "10%", "20%", "35%", "50%+"]
LAND_GREY = "#d4d4d4"

UK_EXTENT = QgsRectangle(-20000, 0, 680000, 1230000)   # BNG: N. Ireland to Shetland

try:
    MM = Qgis.LayoutUnit.Millimeters        # QGIS 3.30+
except AttributeError:
    MM = QgsUnitTypes.LayoutMillimeters


# ------------------------------------------------------------------ helpers
def fill(color, outline=None, width="0.05", no_outline=False):
    props = {"color": color, "outline_color": outline or color, "outline_width": width}
    if no_outline:
        props["outline_style"] = "no"
    return QgsFillSymbol.createSimple(props)


def ramp_renderer(layer, band):
    fcn = QgsColorRampShader(STOPS[0], STOPS[-1])
    try:
        fcn.setColorRampType(Qgis.ShaderInterpolationMethod.Linear)
    except AttributeError:
        fcn.setColorRampType(QgsColorRampShader.Interpolated)
    fcn.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), t)
                              for v, c, t in zip(STOPS, COLOURS, TICKS)])
    fcn.setClip(False)                       # values above 50% use the darkest colour
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(fcn)
    layer.setRenderer(QgsSingleBandPseudoColorRenderer(layer.dataProvider(), band, shader))
    layer.resampleFilter().setZoomedInResampler(QgsBilinearRasterResampler())
    layer.resampleFilter().setZoomedOutResampler(QgsBilinearRasterResampler())


def colour_at(p):
    """Colour at position p (0-1) along the bar - same interpolation as the map ramp."""
    seg = min(int(p * (len(COLOURS) - 1)), len(COLOURS) - 2)
    t = p * (len(COLOURS) - 1) - seg
    a, b = QColor(COLOURS[seg]), QColor(COLOURS[seg + 1])
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t)).name()


def add_label(layout, text, x, y, w, h, size, bold=False, italic=False,
              color="#1f1f1f", halign=Qt.AlignLeft):
    lab = QgsLayoutItemLabel(layout)
    lab.setText(text)
    font = QFont("Arial")
    font.setBold(bold)
    font.setItalic(italic)
    try:
        fmt = QgsTextFormat()
        fmt.setFont(font)
        fmt.setSize(size)
        fmt.setColor(QColor(color))
        lab.setTextFormat(fmt)
    except AttributeError:                   # QGIS < 3.24
        font.setPointSizeF(size)
        lab.setFont(font)
        lab.setFontColor(QColor(color))
    lab.setHAlign(halign)
    lab.attemptMove(QgsLayoutPoint(x, y, MM))
    lab.attemptResize(QgsLayoutSize(w, h, MM))
    layout.addLayoutItem(lab)
    return lab


def add_rect(layout, x, y, w, h, color):
    shape = QgsLayoutItemShape(layout)
    shape.setShapeType(QgsLayoutItemShape.Rectangle)
    shape.setSymbol(fill(color, no_outline=True))
    shape.attemptMove(QgsLayoutPoint(x, y, MM))
    shape.attemptResize(QgsLayoutSize(w, h, MM))
    layout.addLayoutItem(shape)
    return shape


# ------------------------------------------------------------------ base layers
for path in (SURFACES, COAST_PATH):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Not found: {path} - check BASE, and run smooth_surfaces.py first")

project = QgsProject.instance()
project.setCrs(QgsCoordinateReferenceSystem("EPSG:27700"))
tree = project.layerTreeRoot()
old = tree.findGroup(GROUP_NAME)
if old:
    for node in old.findLayers():
        project.removeMapLayer(node.layerId())
    tree.removeChildNode(old)
group = tree.insertGroup(0, GROUP_NAME)

land = QgsVectorLayer(COAST_PATH, "UK land (no data)", "ogr")
land.setSubsetString(COAST_FILTER)
land.setRenderer(QgsSingleSymbolRenderer(fill(LAND_GREY, no_outline=True)))
coastline = QgsVectorLayer(COAST_PATH, "UK coastline", "ogr")
coastline.setSubsetString(COAST_FILTER)
coastline.setRenderer(QgsSingleSymbolRenderer(
    QgsFillSymbol.createSimple({"style": "no", "outline_color": "#7a7a7a", "outline_width": "0.12"})))
for lyr in (coastline, land):
    project.addMapLayer(lyr, False)
    group.addLayer(lyr)

# ------------------------------------------------------------------ layout
manager = project.layoutManager()
existing = manager.layoutByName(LAYOUT_NAME)
if existing:
    manager.removeLayout(existing)
layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName(LAYOUT_NAME)
layout.pageCollection().page(0).setPageSize("A4", QgsLayoutItemPage.Landscape)
manager.addLayout(layout)

PAGE_W, MARGIN, GAP, TOP = 297, 8, 2, 30
map_w = (PAGE_W - 2 * MARGIN - 5 * GAP) / 6
map_h = map_w * UK_EXTENT.height() / UK_EXTENT.width()

maps = []
for i in range(12):
    x = MARGIN + (i % 6) * (map_w + GAP)
    y = TOP + (i // 6) * (map_h + 4)
    mp = QgsLayoutItemMap(layout)
    mp.attemptMove(QgsLayoutPoint(x, y, MM))
    mp.attemptResize(QgsLayoutSize(map_w, map_h, MM))
    mp.setCrs(QgsCoordinateReferenceSystem("EPSG:27700"))
    mp.setKeepLayerSet(True)
    mp.setFrameEnabled(False)
    layout.addLayoutItem(mp)
    mp.zoomToExtent(UK_EXTENT)
    add_label(layout, MONTHS[i], x + 1, y + 1, 14, 6, 9, bold=True)
    maps.append(mp)

# title band (y 5-27): title left, colour-bar legend right - clear of every map
title = add_label(layout, "", MARGIN, 6, 135, 10, 20, bold=True)
subtitle = add_label(layout, "", MARGIN, 16, 135, 7, 11, italic=True, color="#555555")

BAR_X, BAR_Y, BAR_W, BAR_H, SLICES = 150, 11, 100, 4, 100
add_label(layout, "Reporting rate (share of observer-days recording the species)",
          BAR_X, 5, 130, 5, 8, color="#333333")
for s in range(SLICES):
    add_rect(layout, BAR_X + s * BAR_W / SLICES, BAR_Y, BAR_W / SLICES + 0.05, BAR_H,
             colour_at((s + 0.5) / SLICES))
for k, tick in enumerate(TICKS):
    tx = BAR_X + k * BAR_W / (len(TICKS) - 1)
    add_rect(layout, tx - 0.1, BAR_Y + BAR_H, 0.2, 1, "#555555")
    add_label(layout, tick, tx - 7, BAR_Y + BAR_H + 1.2, 14, 4, 7, color="#333333",
              halign=Qt.AlignHCenter)
add_rect(layout, 258, BAR_Y, 5, BAR_H, LAND_GREY)
add_label(layout, "Too few records", 264.5, BAR_Y - 0.2, 26, 5, 7, color="#333333")

dois = ""
if os.path.exists(CITATION):
    with open(CITATION) as f:
        dois = "  |  " + "; ".join(line.split(": ", 1)[-1].strip() for line in f if line.strip())
add_label(layout,
          "Reporting rate = share of eBird observer-days (one observer, one date) on which the "
          f"species was recorded, 2015-2025 combined; records and effort smoothed with a "
          f"{SIGMA_KM} km Gaussian kernel. Grey = fewer than 10 effort-weighted observer-days.\n"
          f"Data: eBird Observation Dataset (Cornell Lab of Ornithology) via GBIF.org{dois}",
          MARGIN, TOP + 2 * map_h + 6, PAGE_W - 2 * MARGIN, 10, 7, color="#555555")


# ------------------------------------------------------------------ export
def export_all():
    os.makedirs(OUT, exist_ok=True)
    exporter = QgsLayoutExporter(layout)
    png = QgsLayoutExporter.ImageExportSettings()
    png.dpi = 250
    pdf = QgsLayoutExporter.PdfExportSettings()
    previous = []
    for common, latin, pattern in SPECIES:
        tif = os.path.join(SURFACES, common.replace(" ", "_") + ".tif")
        if not os.path.exists(tif):
            print(f"skip {common}: {tif} not found")
            continue
        for lyr in previous:                       # drop the last species' layers
            project.removeMapLayer(lyr.id())
        previous = []
        for m, mp in enumerate(maps, start=1):
            lyr = QgsRasterLayer(tif, f"{common} {MONTHS[m - 1]}", "gdal")
            ramp_renderer(lyr, m)
            project.addMapLayer(lyr, False)
            group.addLayer(lyr)
            mp.setLayers([coastline, lyr, land])   # top to bottom
            previous.append(lyr)
        title.setText(common)
        subtitle.setText(f"{latin}  -  {pattern}")
        layout.refresh()
        stem = os.path.join(OUT, common.replace(" ", "_"))
        ok = (exporter.exportToImage(stem + ".png", png) == QgsLayoutExporter.Success
              and exporter.exportToPdf(stem + ".pdf", pdf) == QgsLayoutExporter.Success)
        print(f"{'ok  ' if ok else 'FAIL'} {common}")
    print(f"Atlas pages saved to {OUT}")


export_all()
