let jsonTreeData = null
let checkboxes = ['isOptimizePi', 'isOptimizePiAverage', 'isOptimizeAlpha', 'isOptimizeBL'];
let objectsDependence = {
    'msaText': {'dependence': '', 'value': ''},
    'newickText': {'dependence': '', 'value': ''},
    'pi1': {'dependence': ['isOptimizePi', 'isOptimizePiAverage'], 'value': ''},
    'alpha': {'dependence': ['isOptimizeAlpha'], 'value': ''},
    'categoriesQuantity': {'dependence': '', 'value': ''},
    'coefficientBL': {'dependence': ['isOptimizeBL'], 'value': ''},
    'isOptimizePi': {'dependence': '', 'value': ''},
    'isOptimizePiAverage': {'dependence': '', 'value': ''},
    'isOptimizeAlpha': {'dependence': '', 'value': ''},
    'isOptimizeBL': {'dependence': '', 'value': ''}
};


function getInteger(data) {
    let result = Math.trunc(Number(data) * 10)
    return result === 10 ? 9 : result
}

function setVisibility(id = 'result', visible = true) {
    let element = document.getElementById(id)
    if (visible) {
        element.style.visibility = `visible`;
    } else {
        element.style.visibility = `hidden`;
    }

    return element
}

function setLoader(loaderOn = true) {
    let loader = document.getElementById('loader')
    setVisibility(`result`, !loaderOn)

    if (loaderOn) {
        loader.innerHTML =
            `<div id="loaderCube" class="loaderCube m-9 d-flex gap-2">${'<span></span>'.repeat(4)}</div>`
        loader.classList.add("fixed-center")
    } else {
        loader.innerHTML = ``
        loader.classList.remove("fixed-center")
    }
}

function showAlert(message, duration = 6000, variant = 1) {
    showMessage(message, variant)
    setTimeout(() => {
        showMessage(``, -1);
    }, duration);
}

function validateInput(id, defaultValue){
    let currentElement = document.getElementById(id);
    let currentValue = Number(currentElement.value);
    let  minValue = Number(currentElement.min);
    let  maxValue = Number(currentElement.max);
    if (currentValue <= 0) {
        showAlert(`${currentElement.title}.`);
        currentElement.value = defaultValue;
    } else if (currentValue < minValue && currentValue > 0) {
        showAlert(`${currentElement.title}.`);
        currentElement.value = minValue;
    } else if (currentValue > maxValue) {
        showAlert(`${currentElement.title}.`);
        currentElement.value = maxValue;
    }
}

function loadExample(mode = 0) {
    let newickText = document.getElementById('newickText');
    let msaText = document.getElementById('msaText');
    showMessage(``, -1);

    fetch(`/get_exemple?mode=${mode}`, {
        method: 'GET',
    })
        .then(response => response.json())
        .then(data => {
            msaText.value = data.message[0];
            newickText.value = data.message[1];
        })
        .catch(error => {
            console.error(`Error:`, error);
            showAlert(error.message, 8000);
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
        setVisibility(`result`, true);
        setLoader(false)
        showMessage(``, -1);
        document.getElementById('tree').innerText = ``;
        drawPhylogeneticTree(jsonTreeData);
    }
}

function drawPhylogeneticTree(jsonData) {
    const margin = { top: 20, right: 40, bottom: 20, left: 40 };
    const width = 600 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    const cx = width * .5;
    const cy = height * .5;
    const radius = Math.min(cx, cy);
    let scale = .9;
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
        .attr("style", `width: 100%; height: 100%;`)
        .call(d3.zoom().on("zoom", function (event) {
            svg.attr("transform", event.transform);
        }))
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top}) scale(${scale})`);

    const links = svg.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link");
    links
        .attr("d", isRadialTree ? d3.linkRadial().angle(d => d.x).radius(d => d.y) : d3.linkHorizontal().x(d => d.y).y(d => d.x))
        .style("fill", "none")
        .style("stroke", "silver")
        .style("stroke-width", 1.5)
        .on("mouseover", function(event, d) {
            d3.select(this)
                .style("stroke", "maroon")
            d3.select("#tooltip")
                .style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY - 20}px`)
                .style("opacity", .9)
                .style("visibility",  "visible")
                .html(drawInformation(jsonData[4][d.target.data.name], jsonData[5]["List for sorting"], false, 1, jsonData[6]["Sequence length"]));
        })
        .on("mouseout", function() {
            d3.select(this)
                .style("stroke", "silver")
            d3.select("#tooltip")
                .style("opacity", 0)
                .style("visibility",  "hidden");
        })
        .on("click", function(event, d) {
            document.getElementById('branchInfo').innerHTML = drawInformation(jsonData[4][d.target.data.name], jsonData[5]["List for sorting"], true, 1, jsonData[6]["Sequence length"]);
        });
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
                .style("opacity", .9)
                .style("visibility",  "visible")
                .html(drawInformation(jsonData[1][d.data.name], jsonData[2]["List for sorting"], false, 0, jsonData[6]["Sequence length"]));
        })
        .on("mouseout", function(event, d) {
            d3.select(this)
                .style("fill", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 0, sizeFactor))
                .attr("r", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 2, sizeFactor))
            d3.select("#tooltip")
                .style("opacity", 0)
                .style("visibility",  "hidden");
        })
        .on("click", function(event, d) {
            document.getElementById('nodeInfo').innerHTML = drawInformation(jsonData[1][d.data.name], jsonData[2]["List for sorting"], true, 0, jsonData[6]["Sequence length"]);
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
    console.log(`Error:`, error);
    showAlert(error.message, 8000);
}

function drawInformation(jsonData, sortingList, summary = true, mode = 0, sequenceLength = 0) {
    const fullColorList = ["crimson", "orangered", "darkorange", "gold", "yellowgreen", "forestgreen", "mediumturquoise",
        "dodgerblue", "slateblue", "darkviolet"];
    const shortColorList = {"A": "crimson", "L": "darkorange", "G": "forestgreen", "P": "slateblue"}
    const headersForShortColorList = ["Ancestral Comparison", ]
    const informationObjects = ['Node', 'Branch']
    let table = '';
    let result = '';

    sortingList.forEach(header => {
        let value = ``;
        let jsonValue = jsonData[header];
        result += `<tr><th class="p-2 w-auto tborder-2">${header}</th>`;
        if (typeof jsonValue === "object" && !headersForShortColorList.includes(header))
            {Object.values(jsonValue).forEach(i => {
                value += `<td style="color: ${fullColorList[getInteger(i)]}" class="w-auto text-center">${i}</td>`;
                })
            }
        else if (typeof jsonValue === "object" && headersForShortColorList.includes(header))
            {Object.values(jsonValue).forEach(i => {
                value += `<td style="color: ${shortColorList[i]}" class="w-auto text-center">${i}</td>`;
        }
            )}
        // else {value = `<td class="w-auto text-center">${jsonValue}</td>`}
        result += `<th class="p-2 w-auto">${value}</th></tr>`;
    });

    if (sequenceLength > 0) {
        result += `<tr><th class="p-2 w-auto tborder-2">Index</th>`;
        for (let i = 0; i < sequenceLength; i++) {
            result += `<td style="color: slateblue"  class="w-auto text-center">${i}</td></tr>`;
        }
    }

    if (summary) {
        table = `<details open>
        <summary class="w-100 form-control btn btn-outline-success bg-success-subtle text-success border-0 rounded-pill">
        <span class="arrow">▼</span>
        ${informationObjects[mode]} information
        </summary><table class="w-97 m-3 p-4 h7">${result}</table></details>`
    } else {
        table = `<table class="w-60 h8">${result}</table>`;
    }
    return table;
}

function drawLogLikelihood(jsonData) {
    let result = `<div class="w-100 flex-row form-control btn btn-outline-success bg-success-subtle text-success border-0 rounded-pill" 
            onclick="copyValue('logLikelihoodValue', 7)" title="click here to copy the value of log-Likelihood to the clipboard">
                Tree Log-Likelihood: <span id="logLikelihoodValue" class="badge bg-success" onclick="copyValue(this.id, 7)">${jsonData[0]}</span>
            </div>`
    document.getElementById('logLikelihood').innerHTML = result;
    return result;
}

function copyValue(id, variant = 5) {
    let logLikelihood = document.getElementById(id).textContent
    navigator.clipboard.writeText(logLikelihood).then(function() {
            showAlert(`Tree log-likelihood successfully copied to clipboard<br><br>${logLikelihood}`, 7000, variant);
        }, function(err) {
            showAlert(`An error occurred while copying tree log-likelihood: ${err}`);
        });
}

function drawFileList(jsonData) {
    let headersRow = ``;
    let firstRow = ``;
    let secondRow = ``;
    Object.entries(jsonData).forEach(([key, value]) => {
        headersRow += `<th class="p-1 w-auto">${key}</th>`;
        firstRow += `<th class="p-1 w-auto">${value[0]}</th>`;
        secondRow += `<th class="p-1 w-auto">${value[1]}</th>`;
    });
    let table = `<details open>
        <summary class="w-100 form-control btn btn-outline-success bg-success-subtle text-success border-0 rounded-pill">
        <span class="arrow">▼</span>
        View/Download Results
        </summary>
        <table class="w-97 m-3 p-4 h7">
        <tr>${headersRow}</tr>
        <tr>${secondRow}</tr>
        <tr>${firstRow}</tr>
        </table></details>`;

    document.getElementById('fileList').innerHTML = table;
    return table;
}

function showResponse(jsonData, mode = 0) {
    const actions = ['draw_tree', 'compute_likelihood_of_tree', 'create_all_file_types']
    const dictActions = {'draw_tree': drawPhylogeneticTree, 'compute_likelihood_of_tree': drawLogLikelihood, 'create_all_file_types': drawFileList}

    document.getElementById('title').innerHTML = jsonData['title'];
    completeFormFilling(jsonData['form_data']);


    if (mode === 0) {
        Object.entries(dictActions).forEach(([key, func]) => func(jsonData[key]));
    } else {
        dictActions[actions[mode-1]](jsonData[actions[mode-1]]);
    }

    setVisibility(`result`, true);
}


function makeTree(mode = 0) {
    const newickText = document.getElementById(`newickText`);
    const msaText = document.getElementById(`msaText`);
    const categoriesQuantity = document.getElementById(`categoriesQuantity`);
    const alpha = document.getElementById(`alpha`);
    const pi1 = document.getElementById(`pi1`);
    const coefficientBL = document.getElementById(`coefficientBL`);
    const isOptimizePi = document.getElementById(`isOptimizePi`)
    const isOptimizePiAverage = document.getElementById(`isOptimizePiAverage`)
    const isOptimizeAlpha = document.getElementById(`isOptimizeAlpha`)
    const isOptimizeBL = document.getElementById(`isOptimizeBL`)
    const formData = new FormData();
    formData.append(`newickText`, newickText.value.trim());
    formData.append(`msaText`, msaText.value.trim());
    formData.append(`categoriesQuantity`, categoriesQuantity.value.trim());
    formData.append(`alpha`, alpha.value.trim());
    formData.append(`pi1`, pi1.value.trim());
    formData.append(`coefficientBL`, coefficientBL.value.trim());
    formData.append(`isOptimizePi`, +isOptimizePi.checked);
    formData.append(`isOptimizePiAverage`, +isOptimizePiAverage.checked);
    formData.append(`isOptimizeAlpha`, +isOptimizeAlpha.checked);
    formData.append(`isOptimizeBL`, +isOptimizeBL.checked);

    jsonTreeData = null

    setVisibilityLoader(true);
    setAccessibility();
    setVisibility(`result`, false);

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
            setAccessibility();

            typeof data.message === "object" ? showResponse(data.message, mode) : showAlert(data.message, 8000);
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
    document.getElementById('tree').innerText = ``;
    document.getElementById('branchInfo').innerText = ``;
    document.getElementById('nodeInfo').innerText = ``;
    document.getElementById('logLikelihood').innerText = ``;
    document.getElementById('fileList').innerText = ``;
    showMessage(``, -1);
}

// function getRandomLogo(maxValue = 4) {
//     let randomValue = Math.floor(Math.random() * maxValue) + 1;
//     document.getElementById(`logo`).innerText = `{{nwt.logo(${randomValue})}}`;
// }
//
function gedIdentifiers(id = ``) {
    if (!!id) {
        return [id];
    } else {
        return [`theButton`, `theСleaningButton`, `theExampleButton`, `msaText`, `msaTextFile`, `newickText`,
            `newickTextFile`, 'alpha', `categoriesQuantity`, `pi1`, `coefficientBL`, `isOptimizePi`, `isOptimizePiAverage`,
            `isOptimizeAlpha`, `isOptimizeBL`];
    }
}

function completeFormFilling(formData) {
    Object.entries(objectsDependence).forEach(([id, info]) => {
        let element = document.getElementById(id);
        if (checkboxes.includes(id)) {
            element.checked = Boolean(formData[id]);
        } else {
            element.value = formData[id];
        }
        let disabled = 0
        Object.entries(info['dependence']).forEach((checkboxId) => formData[checkboxId[1]] ? disabled += 1 : disabled += 0);
        element.disabled = Boolean(disabled)
    });
}

function onChangingCheckbox(id, value) {
    let element = document.getElementById(id);
    let checkboxesGroups = {'pi1': ['isOptimizePi', 'isOptimizePiAverage'], 'alpha': ['isOptimizeAlpha'], 'coefficientBL': ['isOptimizeBL']};
    if (checkboxes.includes(id)) {
        Object.entries(checkboxesGroups).forEach(([key, valueList]) => {
            if (valueList.includes(id)) {
                valueList.forEach(elementId => id !== elementId ? document.getElementById(elementId).checked = false : element.checked = Boolean(value));
                setAccessibility(key, element.checked);
            }

        });
    } else {
        element.value = value;
    }
}
// function onChangingCheckbox(id, value) {
//     let element = document.getElementById(id);
//     let objectsD = {'pi1': ['isOptimizePi', 'isOptimizePiAverage'], 'alpha': ['isOptimizeAlpha'], 'coefficientBL': ['isOptimizeBL']};
//     if (checkboxes.includes(id)) {
//         Object.entries(objectsD).forEach(([key, valueList]) => {
//             if (valueList.includes(id)) {
//                 valueList.forEach(elementId => id !== elementId ? element.checked = Boolean(value) : document.getElementById(elementId).checked = false)
//             }
//             // setAccessibility(key, element.checked);
//         });
//     } else {
//         element.value = value;
//     }
// }

function setAccessibility(id = ``, value = null) {
    let elementIdentifiers = gedIdentifiers(id);
    elementIdentifiers.forEach(elementId => {
        let element = document.getElementById(elementId);
        if (value === null) {
            element.disabled = !element.disabled;
        } else {
            element.disabled = value;
        }
    })
}

function showMessage(message = null, variant = 1) {

    let elementNames = [`divInfo`, `divDanger`, `divWarning`, `divSuccess`, `divSecondary`, `divLight`, `divDark`, `divPrimary`];
    let classes = [`fixed-center`, `h-30`, `w-30`]
    for (let i = 0; i < elementNames.length; i++) {
        let visible = variant === i
        let element = setVisibility(elementNames[i], visible);
        if (visible) {
            classes.forEach(currentClass => {
                element.classList.add(currentClass);
            })
            element.innerHTML = message
        } else {
            classes.forEach(currentClass => {
                element.classList.remove(currentClass);
            })
            element.innerHTML = ``
        }
    }
}

function formCleaning(args) {
    let elementNames = {'value': [`newickText`, `msaText`], 'innerHTML': [`tree`, 'branchInfo', `nodeInfo`, `logLikelihood`, `fileList`],
        'setDefault': [`pi1`, `alpha`, `categoriesQuantity`, `coefficientBL`]};
    for (let i = 0; i < elementNames.value.length; i++) {
        document.getElementById(elementNames.value[i]).value = ``;
    }
    for (let i = 0; i < elementNames.innerHTML.length; i++) {
        document.getElementById(elementNames.innerHTML[i]).innerHTML = ``;
    }
    for (let i = 0; i < elementNames.setDefault.length; i++) {
        document.getElementById(elementNames.setDefault[i]).value = args[i];
    }
    showMessage(``, -1);
}

function test(testData) {
    const formData = new FormData();
    formData.append(`svgData`, testData);

    showMessage(``, -1);
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
            showAlert(error.message, 8000);
        });
}
