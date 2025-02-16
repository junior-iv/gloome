function convertJSONToTable(jsonData) {
    let headers = Object.keys(jsonData);
    let table = `<details class="w-95 h-100 h6" open><summary>Node information</summary><table class="w-97 p-4 tborder table-danger">`;

    headers.forEach(header => {
        let colors = ["crimson", "orangered", "darkorange", "gold", "yellowgreen", "forestgreen",
            "mediumturquoise", "dodgerblue", "slateblue", "darkviolet"]
        let value = ``;
        let jsonValue = jsonData[header];
        table += `<tr><th class="p-2 h6 w-auto tborder-2 table-danger">${header}</th>`;
        typeof jsonValue === "object" ? Object.values(jsonValue).forEach(i => {
            value += `<td style="color: ${colors[Math.floor(i * 9)]}" class="h6 w-auto text-center tborder-1 table-danger bg-light">${i}</td>`;
            // value += `<td style="color: ${colors[Math.floor((i < 0.25 ? 1 : i) * 6)]}" class="h6 w-auto text-center tborder-1 table-danger bg-light">${i}</td>`;
        }) : value = `<td class="h6 w-auto text-center">${jsonValue}</td>`;
        table += `<th>${value}</th></tr>`;
    });

    table += `</table></details>`;
    document.getElementById('nodeInfo').innerHTML = table;
}

function loadExample(mode = 1) {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');

    fetch(`/get_exemple?mode=${mode}`, {
        method: 'GET',
    })
        .then(response => response.json())
        .then(data => {
            patternMSA.innerHTML = data.message[0];
            newickText.innerHTML = data.message[1];
        })
        .catch(error => {
            console.error(`Error:`, error);
            showMessage(3, error.message);
        });
}

function getNodeStyle(d, nodeType, mode = 0){
    const answers = [["crimson", "darkorange", "forestgreen"], ["coral", "gold", "limegreen"], [20, 15, 10], [22, 17, 12]]
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

function phylogeneticTree(jsonData) {
    const margin = { top: 20, right: 40, bottom: 20, left: 40 };
    const width = 600 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;
    let scale = 0.9;
    const svg =  d3.select("#tree")
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .call(d3.zoom().on("zoom", function (event) {
                svg.attr("transform", event.transform)
            }))
        .append("g")
            .attr("transform", `translate(${margin.left}, ${margin.top}) scale(${scale})`);

    const tree = d3.tree().size([height, width]);
    const root = d3.hierarchy(jsonData[0]);
    tree(root);

    svg.selectAll(".link")
        .data(root.links())
        .enter().append("path")
        .attr("class", "link")
        .attr("d", d3.linkHorizontal().x(d => d.y).y(d => d.x))
        .style("fill", "none")
        .style("stroke", "silver")
        .style("stroke-width", 3)
        .each(function(d) {
            const midpointX = (d.source.y + d.target.y) / 2;
            const midpointY = (d.source.x + d.target.x) / 2;

            svg.append("text")
                .attr("dy", 6)
                .attr("dx", -12)
                .attr("x", midpointX)
                .attr("y", midpointY)
                .text(`[${d.target.data.distance}]`)
                .style("font-size", "1em")
                .style("fill", "navy");
        });

    const nodes = svg.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", "node")
        .attr("transform", d => `translate(${d.y}, ${d.x})`);

    nodes.append("circle")
        .attr("r", d => getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 2))
        .style("fill", d => getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 0))
        .style("stroke", "steelblue")
        .style("stroke-width", 2)
        .on("mouseover", function(event, d) {
            d3.select(this).style("fill", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 1))
                .attr("r", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 3))
            d3.select("#tooltip")
                .style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY - 20}px`)
                .style("opacity", 1)
                .html(d.data.info);
        })
        .on("mouseout", function(event, d) {
            d3.select(this).style("fill", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 0))
                .attr("r", getNodeStyle(d, jsonData[1][d.data.name]["Node type"], 2))
            d3.select("#tooltip")
                .style("opacity", 0);
        })
        .on("click", function(event, d) {
            convertJSONToTable(jsonData[1][d.data.name]);
        })

    nodes.append("text")
      .attr("dy", -18)
      .attr("x", d => d.children ? 12 : 0)
      .style("text-anchor", d => d.children ? "start" : "start")
      .style("font-size", "1.25em")
      .style("fill", "darkslategray")
      .text(d => d.data.name);
}

function initialize_variables() {
    const newickText = document.getElementById(`newickText`);
    const patternMSA = document.getElementById(`patternMSA`);
    const formData = new FormData();
    formData.append(`newickText`, newickText.value.trim());
    formData.append(`patternMSA`, patternMSA.value.trim());

    const loaderID = `loaderCube`;
    setVisibilityLoader(true, loaderID);

    return {"formData": formData, "loaderID": loaderID}
}

function createAllFileTypes() {
    let funcData = initialize_variables()

    fetch('/create_all_file_types', {
        method: `POST`,
        body: funcData.formData
    })
        .then(response => response.json())
        .then(data => {
            setVisibilityLoader(false, funcData.loaderID);
            showMessage(1, data.message)
        })
        .catch(error => {
            setVisibilityLoader(false, funcData.loaderID);
            console.error(`Error:`, error);
            showMessage(3, error.message)
        });
}

function makeTree(mode = 0) {
    let funcData = initialize_variables()
    let absolutePath = [`/draw_tree`, `/compute_likelihood_of_tree`][mode]

    fetch(absolutePath, {
        method: `POST`,
        body: funcData.formData
    })
        .then(response => response.json())
        .then(data => {
            setVisibilityLoader(false, funcData.loaderID);
            mode === 0 ? phylogeneticTree(data.message) : showMessage(1, data.message)
        })
        .catch(error => {
            setVisibilityLoader(false, funcData.loaderID);
            console.error(`Error:`, error);
            showMessage(3, error.message)
        });
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

function setVisibilityLoader(visible = true, loaderID) {
    if (visible) {
        document.getElementById('tree').innerText = '';
        document.getElementById(loaderID).classList.remove(`invisible`);
        hide_all();
    } else {
        document.getElementById(loaderID).classList.add(`invisible`);
    }
}

function hide_all() {
    let elementNames = [`divInfo`, `divDanger`, `divWarning`, `divSuccess`, `divSecondary`];
    for (let i = 0; i < elementNames.length; i++) {
        document.getElementById(elementNames[i]).style.visibility = `hidden`;
    }
}

function showMessage(variant = 1, message = null) {
    let elementNames = [`divInfo`, `divDanger`, `divWarning`, `divSuccess`, `divSecondary`];
    for (let i = 0; i < elementNames.length; i++) {
        if (variant === i + 1) {
            document.getElementById(elementNames[i]).style.visibility = `visible`;
        } else {
            document.getElementById(elementNames[i]).style.visibility = `hidden`;
        }
        document.getElementById(elementNames[i]).innerHTML = message;
    }
}

function clearForm() {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');
    newickText.innerHTML = '';
    patternMSA.innerHTML = '';
}

function test(testData) {
    const formData = new FormData();
    formData.append(`svgData`, testData);

    const loaderID = `loaderCube`;
    hide_all();
    // document.getElementById('tree').innerText = ''
    setVisibilityLoader(true, loaderID);

    fetch(`/test`, {
        method: `POST`,
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            // document.getElementById('tree').data = data.message;
        })
        .catch(error => {
            setVisibilityLoader(false, loaderID);
            console.error(`Error:`, error);
            showMessage(3, error.message)
        });
}
