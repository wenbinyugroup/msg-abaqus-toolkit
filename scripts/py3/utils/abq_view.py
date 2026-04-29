# -*- coding: utf-8 -*-

"""Helpers for Abaqus viewport, view, and display configuration."""

from abaqus import *
from abaqusConstants import *


def current_viewport(vp=None):
    """Return the requested viewport or the current Abaqus viewport.

    Parameters
    ----------
    vp : object, optional
        Existing viewport handle. When provided it is returned unchanged.

    Returns
    -------
    object or None
        Abaqus viewport handle, or ``None`` when no GUI viewport is active.
    """
    if vp is not None:
        return vp

    try:
        return session.viewports[session.currentViewportName]
    except Exception:
        return None


def current_viewport_name():
    """Return the current Abaqus viewport name when available."""
    try:
        return session.currentViewportName
    except Exception:
        return None


def displayed_object(vp=None):
    """Return the object currently shown in a viewport."""
    viewport = current_viewport(vp)
    if viewport is None:
        return None
    try:
        return viewport.displayedObject
    except Exception:
        return None


def displayed_part_name(vp=None):
    """Return the displayed part name from the active viewport."""
    obj = displayed_object(vp)
    try:
        return obj.name
    except Exception:
        return None


def set_displayed_object(displayed_object, vp=None):
    """Show an object in a viewport when one exists."""
    viewport = current_viewport(vp)
    if viewport is not None and displayed_object is not None:
        viewport.setValues(displayedObject=displayed_object)
    return viewport


def set_named_view(view_name, vp=None):
    """Apply a named Abaqus view preset."""
    viewport = current_viewport(vp)
    if viewport is None:
        return None

    viewport.view.setValues(session.views[view_name])
    return viewport


def fit_view(vp=None):
    """Fit the current object into the viewport."""
    viewport = current_viewport(vp)
    if viewport is not None:
        viewport.view.fitView()
    return viewport


def apply_color_mapping(clr, vp=None, initial_color='#BDBDBD'):
    """Apply an Abaqus color mapping in the active viewport."""
    viewport = current_viewport(vp)
    if viewport is None or clr is None:
        return viewport

    viewport.enableMultipleColors()
    viewport.setColor(initialColor=initial_color)
    viewport.setColor(colorMapping=viewport.colorMappings[clr])
    viewport.disableMultipleColors()
    return viewport


def set_sg_view(vp=None, nsg=3, obj=None, clr=None):
    """Set the standard SG viewing direction and optional color mapping.

    Parameters
    ----------
    vp : object, optional
        Target viewport.
    nsg : int, optional
        SG dimension. ``1`` and ``2`` use the YZ-oriented view; ``3`` uses
        the default 3D oblique view.
    obj : object, optional
        Object to display before adjusting the view.
    clr : str, optional
        Abaqus color mapping name to apply.

    Returns
    -------
    object or None
        Abaqus viewport handle when available.
    """
    viewport = set_displayed_object(obj, vp)
    if viewport is None:
        return None

    if nsg in (1, 2):
        viewport.view.setViewpoint(
            viewVector=(1.0, 0.0, 0.0),
            cameraUpVector=(0.0, 0.0, 1.0),
        )
    elif nsg == 3:
        viewport.view.setViewpoint(
            viewVector=(1.0, 0.8, 0.6),
            cameraUpVector=(0.0, 0.0, 1.0),
        )

    apply_color_mapping(clr, vp=viewport)
    fit_view(vp=viewport)
    return viewport


def configure_part_display(vp=None, sectionAssignments=None,
                           engineeringFeatures=None, mesh=None,
                           referenceRepresentation=None,
                           meshTechnique=None):
    """Apply part-display options to a viewport."""
    viewport = current_viewport(vp)
    if viewport is None:
        return None

    display_kwargs = {}
    if sectionAssignments is not None:
        display_kwargs['sectionAssignments'] = sectionAssignments
    if engineeringFeatures is not None:
        display_kwargs['engineeringFeatures'] = engineeringFeatures
    if mesh is not None:
        display_kwargs['mesh'] = mesh
    if display_kwargs:
        viewport.partDisplay.setValues(**display_kwargs)

    geometry_kwargs = {}
    if referenceRepresentation is not None:
        geometry_kwargs['referenceRepresentation'] = referenceRepresentation
    if geometry_kwargs:
        viewport.partDisplay.geometryOptions.setValues(**geometry_kwargs)

    mesh_kwargs = {}
    if meshTechnique is not None:
        mesh_kwargs['meshTechnique'] = meshTechnique
    if mesh_kwargs:
        viewport.partDisplay.meshOptions.setValues(**mesh_kwargs)

    return viewport


def configure_assembly_display(vp=None, mesh=None, optimizationTasks=None,
                               geometricRestrictions=None,
                               stopConditions=None, meshTechnique=None):
    """Apply assembly-display options to a viewport."""
    viewport = current_viewport(vp)
    if viewport is None:
        return None

    display_kwargs = {}
    if mesh is not None:
        display_kwargs['mesh'] = mesh
    if optimizationTasks is not None:
        display_kwargs['optimizationTasks'] = optimizationTasks
    if geometricRestrictions is not None:
        display_kwargs['geometricRestrictions'] = geometricRestrictions
    if stopConditions is not None:
        display_kwargs['stopConditions'] = stopConditions
    if display_kwargs:
        viewport.assemblyDisplay.setValues(**display_kwargs)

    mesh_kwargs = {}
    if meshTechnique is not None:
        mesh_kwargs['meshTechnique'] = meshTechnique
    if mesh_kwargs:
        viewport.assemblyDisplay.meshOptions.setValues(**mesh_kwargs)

    return viewport


def split_viewport_left_right(vp=None, new_viewport_name='Viewport: 2'):
    """Split the drawing area into two side-by-side viewports.

    Returns
    -------
    tuple
        ``(left_viewport, right_viewport)``.
    """
    viewport = current_viewport(vp)
    if viewport is None:
        return (None, None)

    da = session.drawingArea
    width = da.width / 2.0
    height = da.height
    left_origin = da.origin
    right_origin = (da.origin[0] + width, da.origin[1])

    viewport.setValues(origin=left_origin, width=width, height=height)

    if new_viewport_name in session.viewports:
        vp_right = session.viewports[new_viewport_name]
        vp_right.setValues(origin=right_origin, width=width, height=height)
    else:
        vp_right = session.Viewport(
            name=new_viewport_name,
            origin=right_origin,
            width=width,
            height=height,
        )

    return (viewport, vp_right)


def configure_viewport_annotations(vp=None, family='consolas',
                                   style='medium', size=140,
                                   legend_min_max=ON,
                                   legend_decimal_places=6,
                                   legend_background_style=TRANSPARENT):
    """Apply common annotation font settings to a viewport."""
    viewport = current_viewport(vp)
    if viewport is None:
        return None

    view_font = (
        '-*-' + family + '-' + style + '-r-normal-*-*-' + str(size) +
        '-*-*-m-*-*-*'
    )
    viewport.viewportAnnotationOptions.setValues(
        triadFont=view_font,
        legendFont=view_font,
        titleFont=view_font,
        stateFont=view_font,
        legendMinMax=legend_min_max,
        legendDecimalPlaces=legend_decimal_places,
        legendBackgroundStyle=legend_background_style,
    )
    return viewport


def configure_odb_contour_display(vp=None, variable_label='EN',
                                  component='EN11',
                                  output_position=ELEMENT_NODAL,
                                  plot_state=CONTOURS_ON_DEF,
                                  visible_edges=None, restore=False):
    """Configure a viewport for contour display of an ODB variable."""
    viewport = current_viewport(vp)
    if viewport is None:
        return None

    viewport.odbDisplay.setPrimaryVariable(
        variableLabel=variable_label,
        outputPosition=output_position,
        refinement=(COMPONENT, component),
    )
    if restore:
        viewport.restore()
    viewport.odbDisplay.display.setValues(plotState=plot_state)
    if visible_edges is not None:
        viewport.odbDisplay.commonOptions.setValues(visibleEdges=visible_edges)
    return viewport


def make_current(vp=None):
    """Make a viewport current."""
    viewport = current_viewport(vp)
    if viewport is not None:
        viewport.makeCurrent()
    return viewport


def set_linked_viewports(link_viewports=True, field_output=None):
    """Configure linked viewport behavior."""
    session.linkedViewportCommands.setValues(linkViewports=link_viewports)
    if field_output is not None:
        session.linkedViewportCommands.setValues(fieldOutput=field_output)
