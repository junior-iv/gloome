function clearForm() {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');
    newickText.innerHTML = ''
    patternMSA.innerHTML = ''
}

function loadExample() {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');
    newickText.innerHTML = '(A:0.1,((E:0.1,(F1:0.1,F2:0.1):0.2):0.2,((D1:1.1,D2:0.1):0.12,((B1:0.1,B2:0.1):0.2,C:0.1):0.2):0.2):0.2);'
    patternMSA.innerHTML = '>A\n' +
        '11101010111000101011111011111\n' +
        '>B1\n' +
        '11111011000100110110000011111\n' +
        '>B2\n' +
        '10110001111001110101010111111\n' +
        '>C\n' +
        '11011000000101111000101000001\n' +
        '>D1\n' +
        '01011000111110101010101010001\n' +
        '>D2\n' +
        '01011000111110101010101010001\n' +
        '>E\n' +
        '01010101100011111011011111011\n' +
        '>F1\n' +
        '10000101010110001101010101111\n' +
        '>F2\n' +
        '10000101010000000101010101111\n'
}

function loadExample2() {
    let newickText = document.getElementById('newickText');
    let patternMSA = document.getElementById('patternMSA');
    newickText.innerHTML = '(((Langur:0.081,Baboon:0.033):0.021,Human:0.064):0.01,(Cow:0.240,Horse:0.63):0.106);'
    patternMSA.innerHTML = '>Langur\n' +
        'KIFERCELARTLKKLGLDGYKGVSLANWVCLAKWESGYNTEATNYNPGDESTDYGIFQINSRYWCNNGKPGAVDACHISCSALLQNNIADAVACAKRVVSDQGIRAWVAWRNHCQNKDVSQYVKGCGV\n' +
        '>Baboon\n' +
        'KIFERCELARTLKRLGLDGYRGISLANWVCLAKWESDYNTQATNYNPGDQSTDYGIFQINSHYWCNDGKPGAVNACHISCNALLQDNITDAVACAKRVVSDQGIRAWVAWRNHCQNRDVSQYVQGCGV\n' +
        '>Human\n' +
        'KVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAGDRSTDYGIFQINSRYWCNDGKPGAVNACHLSCSALLQDNIADAVACAKRVVRDQGIRAWVAWRNRCQNRDVRQYVQGCGV\n' +
        '>Cow\n' +
        'KVFERCELARTLKKLGLDGYKGVSLANWLCLTKWESSYNTKATNYNPSSESTDYGIFQINSKWWCNDGKPNAVDGCHVSCSELMENDIAKAVACAKKIVSEQGITAWVAWKSHCRDHDVSSYVEGCTL\n' +
        '>Horse\n' +
        'KVFSKCELAHKLKAQEMDGFGGYSLANWVCMAEYESNFNTRAFNGKNANGSSDYGLFQLNNKWWCKDNKRSSSNACNIMCSKLLDENIDDDISCAKRVVRDKGMSAWKAWVKHCKDKDLSEYLASCNL'
}

function computeLikelihoodOfTree() {
    const newickText = document.getElementById('newickText');
    const patternMSA = document.getElementById('patternMSA');
    const formData = new FormData();
    formData.append('newickText', newickText.value.trim());
    formData.append('patternMSA', patternMSA.value.trim());

    const loaderID = 'loaderCube';
    setVisibilityLoader(true, loaderID);

    fetch('/compute_likelihood_of_tree', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            setVisibilityLoader(false, loaderID);
            showMessage(1, data.message)
        })
        .catch(error => {
            setVisibilityLoader(false, loaderID);
            console.error('Error:', error);
            showMessage(3, error.message)
        });
}

function setVisibilityLoader(visible = true, loaderID) {
    if (visible) {
        document.getElementById(loaderID).classList.remove('invisible');

        document.getElementById('divWarning').style.visibility = 'hidden';
        document.getElementById('divDanger').style.visibility = 'hidden';
        document.getElementById('divInfo').style.visibility = 'hidden';
        document.getElementById('divSuccess').style.visibility = 'hidden';
        document.getElementById('divSecondary').style.visibility = 'hidden';
    } else {
        document.getElementById(loaderID).classList.add('invisible');
    }
}

function getLoader() {
    const rnd = Math.floor(Math.random() * 3);
    if (rnd === 0) {return 'loaderCube'}
    else if (rnd === 1) {return 'loaderSpinner'}
    else if (rnd === 2) {return 'loaderGrow'}
}

function showMessage(variant = 1, message = null) {
    let mode = [];
    if (variant === 1) {
        if (message === null) {message = 'YES'}
        mode = ['hidden', 'hidden', 'visible', 'hidden', 'hidden', message];
    } else if (variant === 2) {
        if (message === null) {message = 'NO'}
        mode = ['hidden', 'visible', 'hidden', 'hidden', 'hidden', message];
    } else if (variant === 3) {
        mode = ['visible', 'hidden', 'hidden', 'hidden', 'hidden', message];
    } else if (variant === 4) {
        mode = ['hidden', 'hidden', 'hidden', 'visible', 'hidden', message];
    } else if (variant === 5) {
        mode = ['hidden', 'hidden', 'hidden', 'hidden', 'visible', message];
    }
    document.getElementById('divWarning').style.visibility = mode[0];
    document.getElementById('divWarning').innerHTML = mode[5];
    document.getElementById('divDanger').style.visibility = mode[1];
    document.getElementById('divDanger').innerHTML = mode[5];
    document.getElementById('divInfo').style.visibility = mode[2];
    document.getElementById('divInfo').innerHTML = mode[5];
    document.getElementById('divSuccess').style.visibility = mode[3];
    document.getElementById('divSuccess').innerHTML = mode[5];
    document.getElementById('divSecondary').style.visibility = mode[4];
    document.getElementById('divSecondary').innerHTML = mode[5];
}