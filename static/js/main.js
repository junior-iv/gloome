function clearForm() {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');
    newickText.innerHTML = ''
    patternMSA.innerHTML = ''
}

function loadExample(mode = 1) {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');

    fetch(`/get_exemple?mode=${mode}`, {
        method: 'GET',
    })
        .then(response => response.json())
        .then(data => {
            patternMSA.innerHTML = data.message[0]
            newickText.innerHTML = data.message[1]
        })
        .catch(error => {
            console.error(`Error:`, error);
            showMessage(3, error.message)
        });
}

function phylogeneticTree(treeData) {
    const margin = { top: 20, right: 40, bottom: 20, left: 40 };
    const width = 500 - margin.left - margin.right;
    const height = 500 - margin.top - margin.bottom;
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
    const root = d3.hierarchy(JSON.parse(treeData));
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
        .attr("r", d => d.children ? 15 : 10)
        .style("fill", d => d.children ? "darkorange" : "forestgreen")
        .style("stroke", "steelblue")
        .style("stroke-width", 2)
        .on("mouseover", function(event, d) {
            d3.select(this).style("fill", d => d.children ? "gold" : "limegreen")
            d3.select("#tooltip")
                .style("left", `${event.pageX + 10}px`)
                .style("top", `${event.pageY - 20}px`)
                .style("opacity", 1)
                .html(d.data.info);
        })
        .on("mouseout", function() {
            d3.select(this).style("fill", d => d.children ? "darkorange" : "forestgreen")
            d3.select("#tooltip")
                .style("opacity", 0);
        })
        .on("click", function(event, d) {
            document.getElementById("nodeInfo").innerHTML = d.data.info;
        });

    nodes.append("text")
      .attr("dy", -18)
      .attr("x", d => d.children ? 12 : 0)
      .style("text-anchor", d => d.children ? "start" : "start")
      .style("font-size", "1.25em")
      .style("fill", "darkslategray")
      .text(d => d.data.name);
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

function drawTree() {
    const newickText = document.getElementById(`newickText`);
    const patternMSA = document.getElementById(`patternMSA`);
    const formData = new FormData();
    formData.append(`newickText`, newickText.value.trim());
    formData.append(`patternMSA`, patternMSA.value.trim());

    const loaderID = `loaderCube`;
    hide_all();
    document.getElementById('tree').innerText = ''
    setVisibilityLoader(true, loaderID);

    fetch(`/draw_tree`, {
        method: `POST`,
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            setVisibilityLoader(false, loaderID);
            phylogeneticTree(data.message)
        })
        .catch(error => {
            setVisibilityLoader(false, loaderID);
            console.error(`Error:`, error);
            showMessage(3, error.message)
        });
}

function computeLikelihoodOfTree() {
    const newickText = document.getElementById(`newickText`);
    const patternMSA = document.getElementById(`patternMSA`);
    const formData = new FormData();
    formData.append(`newickText`, newickText.value.trim());
    formData.append(`patternMSA`, patternMSA.value.trim());

    const loaderID = `loaderCube`;
    setVisibilityLoader(true, loaderID);

    fetch(`/compute_likelihood_of_tree`, {
        method: `POST`,
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            setVisibilityLoader(false, loaderID);
            showMessage(1, data.message)
        })
        .catch(error => {
            setVisibilityLoader(false, loaderID);
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
        document.getElementById(loaderID).classList.remove(`invisible`);

        document.getElementById(`divWarning`).style.visibility = `hidden`;
        document.getElementById(`divDanger`).style.visibility = `hidden`;
        document.getElementById(`divInfo`).style.visibility = `hidden`;
        document.getElementById(`divSuccess`).style.visibility = `hidden`;
        document.getElementById(`divSecondary`).style.visibility = `hidden`;
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
        document.getElementById(elementNames[i]).innerText = message;
    }
}