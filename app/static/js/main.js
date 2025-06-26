let jsonTreeData = null

function getInteger(data) {
    let result = Math.trunc(Number(data) * 10)
    return result === 10 ? 9 : result
}

function setLoader(loaderOn = true) {
    if (loaderOn) {
        document.getElementById('loader').innerHTML =
            `<div id="loaderCube" class="loaderCube m-9 d-flex gap-2">${'<span></span>'.repeat(4)}</div>`
    } else {
        document.getElementById('loader').innerHTML = ''
    }
}

function loadExample(mode = 0) {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');
    hide_all();

    fetch(`/get_exemple?mode=${mode}`, {
        method: 'GET',
    })
        .then(response => response.json())
        .then(data => {
            patternMSA.value = data.message[0];
            newickText.value = data.message[1];
        })
        .catch(error => {
            console.error(`Error:`, error);
            showMessage(error.message);
        });
}

function getNodeStyle(d, nodeType, mode = 0, sizeFactor = 1){
    let sizes = [parseInt(20 / sizeFactor), parseInt(15 / sizeFactor), parseInt(10 / sizeFactor)];
    let sizes_with_side = [2 + sizes[0], 2 + sizes[1], 2 + sizes[2]];
    const answers = [["crimson", "darkorange", "forestgreen"], ["coral", "gold", "limegreen"], sizes, sizes_with_side];
    if (nodeType === "root"){
        return answers[mode][0];
    }
    else if (d.children && nodeType !== "root") {
        return answers[mode][1];
    }
    else {
        return answers[mode][2];
    }
}

function reDrawPhylogeneticTree() {
    if (jsonTreeData !== null){
        setLoader(false)
        hide_all();
        document.getElementById('tree').innerText = '';
        document.getElementById('nodeInfo').innerText = '';
        drawPhylogeneticTree(jsonTreeData);
    }
}

function drawPhylogeneticTree(jsonData) {
    const margin = { top: 20, right: 40, bottom: 20, left: 40 };
    const width = 600 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    const cx = width * 0.5;
    const cy = height * 0.5;
    const radius = Math.min(cx, cy);
    let scale = 0.9;
    const sizeFactor = jsonData[3]["Size factor"]
    const isRadial = document.getElementById(`isRadialTree`);
    const showDistance = document.getElementById(`showDistanceToParent`);
    const isRadialTree = isRadial.checked;
    const showDistanceToParent = showDistance.checked;
    jsonTreeData = jsonData

    const tree = d3.tree()
    if (isRadialTree) {
        tree.size([2 * Math.PI, radius])
            .separation((a, b) => (a.parent === b.parent ? 1 : 2) / a.depth);
    } else {
        tree.size([height, width]);
    }

    const root = tree(d3.hierarchy(jsonData[0])
        .sort((a, b) => d3.ascending(a.data.name, b.data.name)));

    const svg =  d3.select("#tree")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .attr("viewBox", isRadialTree ? [-cx, -cy, width, height] : [0, 0, width, height])
        .attr("style", `width: 100%; height: auto;`)
        .call(d3.zoom().on("zoom", function (event) {
            svg.attr("transform", event.transform);
        }))
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top}) scale(${scale})`);

    svg.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("d", isRadialTree ? d3.linkRadial().angle(d => d.x).radius(d => d.y) : d3.linkHorizontal().x(d => d.y).y(d => d.x))
        .style("fill", "none")
        .style("stroke", "silver")
        .style("stroke-width", 1.5);

    const nodes = svg.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", isRadialTree ? d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)` : d => `translate(${d.y}, ${d.x})`);

    nodes
        .append("circle")
        .attr("r", d => getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 2, sizeFactor))
        .style("fill", d => getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 0, sizeFactor))
        .style("stroke", "steelblue")
        .style("stroke-width", 2)
        .on("mouseover", function(event, d) {
            d3.select(this)
                .style("fill", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 1, sizeFactor))
                .attr("r", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 3, sizeFactor))
            d3.select("#tooltip")
                .style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY - 20}px`)
                .style("opacity", 1)
                .html(d.data.info);
        })
        .on("mouseout", function(event, d) {
            d3.select(this)
                .style("fill", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 0, sizeFactor))
                .attr("r", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 2, sizeFactor))
            d3.select("#tooltip")
                .style("opacity", 0);
        })
        .on("click", function(event, d) {
            document.getElementById('nodeInfo').innerHTML = convertJSONToTable(jsonData[1][d.data.name], jsonData[2]);
        });

    nodes
        .append("text")
        .style("font-size", d => !d.children ? parseInt(12 / sizeFactor) : parseInt(16 / sizeFactor))
        .style("font-family", "Verdana")
        .style("text-anchor", d => d.children ? "start" : "start")
        .style("font-weight", d => !d.children ? "normal" : "bold")
        .style("fill", function(d) {
            if (jsonData[1][d.data.name]["Node type"] === "root") { return "maroon" }
            else if (jsonData[1][d.data.name]["Node type"] === "node") { return "navy" }
            else { return "black" }
        })
        .attr("dy", d => !d.children ? parseInt(3 / sizeFactor) : parseInt(6 / sizeFactor))
        .attr("dx", d => !d.children ? parseInt(18 / sizeFactor) : parseInt(24 / sizeFactor))
        .text(d => d.data.name);
    if (showDistanceToParent) {
        nodes
            .append("text")
            .style("font-size", parseInt(10 / sizeFactor))
            .style("font-family", "sans-serif")
            .style("text-anchor", "end")
            .style("font-weight", "normal")
            .style("fill", "darkcyan")
            .attr("dy", d => !d.children ? parseInt(3 / sizeFactor) : parseInt(6 / sizeFactor))
            .attr("dx", d => !d.children ? -parseInt(18 / sizeFactor) : -parseInt(24 / sizeFactor))
            .text(d => jsonData[1][d.data.name]["Node type"] !== "root" ? `[${parseFloat(d.data.distance)}]` : ``);
    }
}

function processError(error) {
    setVisibilityLoader(false);
    console.error(`Error:`, error);
    showMessage(error.message);
}

function convertJSONToTable(jsonData, jsonSort) {
    const sortingList = jsonSort["List for sorting"];
    const colors = ["crimson", "orangered", "darkorange", "gold", "yellowgreen", "forestgreen", "mediumturquoise",
        "dodgerblue", "slateblue", "darkviolet"];
    const colorsAS = {"A": "crimson", "G": "darkorange", "L": "forestgreen", "P": "slateblue"}
    let table = `<details class="w-95 h-100 h7" open><summary>Node information</summary><table class="w-97 p-4 tborder table-danger">`;

    sortingList.forEach(header => {
        let value = ``;
        let jsonValue = jsonData[header];
        table += `<tr><th class="p-2 h7 w-auto tborder-2 table-danger">${header}</th>`;
        if (typeof jsonValue === "object" && header !== "Ancestral sequence") {Object.values(jsonValue).forEach(i => {
            value += `<td style="color: ${colors[getInteger(i)]}" class="h7 w-auto text-center tborder-1 table-danger bg-light">${i}</td>`;
        })}
        else if (typeof jsonValue === "object" && header === "Ancestral sequence") {Object.values(jsonValue).forEach(i => {
            value += `<td style="color: ${colorsAS[i]}" class="h7 w-auto text-center tborder-1 table-danger bg-light">${i}</td>`;
        })}
        else {value = `<td class="h7 w-auto text-center">${jsonValue}</td>`}
        table += `<th>${value}</th></tr>`;
    });

    table += `</table></details>`;
    return table;
}

function convertJSONToTableFoLogLikelihood(jsonData) {
    let table = `<details class="w-95 my-2 h-100 h7" open><summary>Log-likelihood information</summary>
                        <table class="w-97 table-success list-group-item-info">`;
    Object.entries(jsonData).forEach(([key, value]) => {
        table += `<tr><th class="text-center w-auto text-break">${key}</th>`;
        table += `<th class="w-auto text-center text-break">${value}</th></tr>`;
    });
    table += `</table></details>`;
    document.getElementById('logLikelihood').innerHTML = table;
    return table;
}

function convertJSONToTableFoFileList(jsonData) {
    let headersRow = ``;
    let firstRow = ``;
    let secondRow = ``;
    Object.entries(jsonData).forEach(([key, value]) => {
        headersRow += `<th  class="text-center w-auto text-break">${key}</th>`;
        firstRow += `<th  class="w-auto text-center text-break">${value[0]}</th>`;
        secondRow += `<th class="w-auto text-center text-break">${value[1]}</th>`;
    });
    let table = `<details class=" my-2 w-95 h-100 h7" open><summary>File list</summary>
             <table class="w-97  table-success list-group-item-info"><tr>${headersRow}</tr><tr>${firstRow}</tr><tr>${secondRow}</tr>
             </table></details>`;
    document.getElementById('fileList').innerHTML = table;
    return table;
}

function showResponse(jsonData, mode = 0) {
    let actions = ['draw_tree', 'compute_likelihood_of_tree', 'create_all_file_types']
    let dictActions = {'draw_tree': drawPhylogeneticTree, 'compute_likelihood_of_tree': convertJSONToTableFoLogLikelihood, 'create_all_file_types': convertJSONToTableFoFileList}
    if (mode === 0) {
        Object.entries(dictActions).forEach(([key, func]) => func(jsonData[key]));
    } else {
        dictActions[actions[mode-1]](jsonData);
        // chooseFunction(jsonData, actions[mode-1])
    }
}


function makeTree(mode = 0) {
    const newickText = document.getElementById(`newickText`);
    const patternMSA = document.getElementById(`patternMSA`);
    const categoriesQuantity = document.getElementById(`categoriesQuantity`);
    const alpha = document.getElementById(`alpha`);
    const formData = new FormData();
    formData.append(`newickText`, newickText.value.trim());
    formData.append(`patternMSA`, patternMSA.value.trim());
    formData.append(`categoriesQuantity`, categoriesQuantity.value.trim());
    formData.append(`alpha`, alpha.value.trim());

    jsonTreeData = null

    setVisibilityLoader(true);
    let absolutePath = ['/execute_all_actions', `/draw_tree`, `/compute_likelihood_of_tree`, '/create_all_file_types'][mode];

    fetch(absolutePath, {
        method: `POST`,
        body: formData
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {response.json()
                .then(data => {throw new Error(data.message)})
                .catch(error => {processError(error)})}
        })
        .then(data => {
            setVisibilityLoader(false);
            typeof data.message === "object" ? showResponse(data.message, mode) : showMessage(data.message, 1);
        })
        .catch(error => {processError(error)});
}

function uploadFile(textAreaName = `newickText`, textFileName = `newickTextFile`) {
    let textFile = document.getElementById(textFileName).files[0];
    let textArea = document.getElementById(textAreaName);
    {
        if (textFile) {
            let reader = new FileReader();

            reader.onload = function(event) {
                textArea.value = event.target.result.trim();
            };
            reader.readAsText(textFile);
        }
    }
}

function setVisibilityLoader(visible = true) {
    setLoader(visible)
    document.getElementById('tree').innerText = '';
    document.getElementById('nodeInfo').innerText = '';
    document.getElementById('logLikelihood').innerText = '';
    document.getElementById('fileList').innerText = '';
    hide_all();
}

function hide_all() {
    let elementNames = [`divInfo`, `divDanger`, `divWarning`, `divSuccess`, `divSecondary`];
    for (let i = 0; i < elementNames.length; i++) {
        document.getElementById(elementNames[i]).style.visibility = `hidden`;
    }
}

function showMessage(message = null, variant = 2) {
    let elementNames = [`divInfo`, `divDanger`, `divWarning`, `divSuccess`, `divSecondary`];
    for (let i = 0; i < elementNames.length; i++) {
        if (variant === i) {
            document.getElementById(elementNames[i]).style.visibility = `visible`;
        } else {
            document.getElementById(elementNames[i]).style.visibility = `hidden`;
        }
        document.getElementById(elementNames[i]).innerHTML = message;
    }
}

function clearForm() {
    let elementNames = {'value': [`newickText`, `patternMSA`], 'innerHTML': [`tree`, `nodeInfo`, `logLikelihood`, `fileList`]};
    for (let i = 0; i < elementNames.value.length; i++) {
        document.getElementById(elementNames.value[i]).value = '';
    }
    for (let i = 0; i < elementNames.innerHTML.length; i++) {
        document.getElementById(elementNames.innerHTML[i]).innerHTML = '';
    }
    hide_all();
}

function test(testData) {
    const formData = new FormData();
    formData.append(`svgData`, testData);

    hide_all();
    // document.getElementById('tree').innerText = ''
    setVisibilityLoader(true);

    fetch(`/test`, {
        method: `POST`,
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // document.getElementById('tree').data = data.message;
        })
        .catch(error => {
            setVisibilityLoader(false);
            console.error(`Error:`, error);
            showMessage(error.message);
        });
}
