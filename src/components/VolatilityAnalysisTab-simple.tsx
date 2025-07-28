// Simplified Term Structure Chart
export const drawSimpleTermStructure = (
  termChartRef: React.RefObject<HTMLDivElement>,
  surfaceData: any[],
  visibleDeltasForTerm: Set<number>,
  currentTheme: any,
  d3: any
) => {
  if (!termChartRef.current || !surfaceData.length) return
  
  // Clear previous
  d3.select(termChartRef.current).selectAll("*").remove()
  
  const margin = { top: 20, right: 80, bottom: 50, left: 50 }
  const width = termChartRef.current.clientWidth - margin.left - margin.right
  const height = termChartRef.current.clientHeight - margin.top - margin.bottom
  
  if (width <= 0 || height <= 0) return
  
  const svg = d3.select(termChartRef.current)
    .append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
  
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`)
  
  // Prepare data - simple ATM volatilities
  const atmData = surfaceData
    .filter(d => d.raw?.atm_bid && d.raw?.atm_ask)
    .map(d => ({
      tenor: d.tenor,
      vol: (d.raw.atm_bid + d.raw.atm_ask) / 2,
      order: ['ON', '1W', '2W', '1M', '2M', '3M', '6M', '9M', '1Y', '18M', '2Y'].indexOf(d.tenor)
    }))
    .filter(d => d.order >= 0)
    .sort((a, b) => a.order - b.order)
  
  if (atmData.length === 0) return
  
  // Scales
  const xScale = d3.scaleBand()
    .domain(atmData.map(d => d.tenor))
    .range([0, width])
    .padding(0.1)
  
  const yScale = d3.scaleLinear()
    .domain([
      Math.min(...atmData.map(d => d.vol)) - 0.5,
      Math.max(...atmData.map(d => d.vol)) + 0.5
    ])
    .range([height, 0])
  
  // Axes
  g.append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale))
    .style("color", currentTheme.textSecondary)
  
  g.append("g")
    .call(d3.axisLeft(yScale).tickFormat(d => `${d}%`))
    .style("color", currentTheme.textSecondary)
  
  // Line
  const line = d3.line()
    .x(d => xScale(d.tenor) + xScale.bandwidth() / 2)
    .y(d => yScale(d.vol))
    .curve(d3.curveCatmullRom)
  
  g.append("path")
    .datum(atmData)
    .attr("fill", "none")
    .attr("stroke", currentTheme.primary)
    .attr("stroke-width", 2)
    .attr("d", line)
  
  // Points
  g.selectAll(".point")
    .data(atmData)
    .enter()
    .append("circle")
    .attr("cx", d => xScale(d.tenor) + xScale.bandwidth() / 2)
    .attr("cy", d => yScale(d.vol))
    .attr("r", 4)
    .attr("fill", currentTheme.background)
    .attr("stroke", currentTheme.primary)
    .attr("stroke-width", 2)
  
  // Title
  g.append("text")
    .attr("x", width / 2)
    .attr("y", -10)
    .attr("text-anchor", "middle")
    .style("font-size", "12px")
    .style("fill", currentTheme.text)
    .text("ATM Volatility Term Structure")
}