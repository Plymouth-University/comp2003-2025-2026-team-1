-- Configure diagram filter to use SVG for PlantUML
function Meta(meta)
  if not meta.diagram then
    meta.diagram = {}
  end
  if not meta.diagram.engine then
    meta.diagram.engine = {}
  end
  -- Configure plantuml to use SVG
  meta.diagram.engine.plantuml = {
    ['mime-type'] = {
      ['image/svg+xml'] = true,
      ['application/pdf'] = false
    }
  }
  return meta
end
