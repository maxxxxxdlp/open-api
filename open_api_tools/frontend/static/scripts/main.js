const getParameterValue = (parameterElement, parameterType) =>
  parameterType === 'string' ?
    parameterElement.getElementsByTagName('input')[0].value :
    (
      parameterElement.getElementsByTagName('input')[0].checked
    ).toString();

const fetchParametersData = (parameters) =>
  pathDetailedInfo.parameters.forEach((parameter, index) => (
    pathDetailedInfo.parameters[index].value =
      getParameterValue(parameters[index], parameter.type)
  ));

const createRequestUrl = () =>
  pathDetailedInfo.parameters.reduce((requestUrl, parameterData) =>
      parameterData.location === 'path' ?
        requestUrl.replace(
          `{${parameterData.name}}`,
          encodeURIComponent(parameterData.value),
        ) :
        `${requestUrl}${parameterData.name}=${encodeURIComponent(
          parameterData.value,
        )}&`,
    `${pathDetailedInfo.server}${pathDetailedInfo.path}?`);

const exposeRequestUrl = (requestUrlElement, requestUrl) =>
  requestUrlElement.classList.remove('hidden') ||
  (
    requestUrlElement.getElementsByTagName('input')[0].value = requestUrl
  );

const showLoadingAnimation = (responseContainer) =>
  responseContainer.classList.remove('hidden') ||
  responseContainer.classList.add('loading');

const showResponse = (responseContainer, response) =>
  responseContainer.classList.remove('loading') ||
  response.text().then(responseHtml => (
    responseContainer.getElementsByClassName(
      'response-content',
    )[0].innerHTML = responseHtml
  ));

(
  () => {

    const parameters = Object.values(
      document.getElementsByClassName('parameter'),
    );
    const requestUrlElement =
      document.getElementsByClassName('request-url')[0];
    const responseContainer = document.getElementById('response');

    document.body.addEventListener('change', (event) => {

      const parameterExamples = event.target.closest('.parameter-examples');
      if (parameterExamples !== null && parameterExamples.value !== '0')
        parameterExamples.parentElement.nextElementSibling.
          getElementsByTagName('input')[0].value =
          parameterExamples.value;

    });

    document.body.addEventListener('click', (event) => {

      if (event.target.closest('.execute-button')) {
        fetchParametersData(parameters);
        const requestUrl = createRequestUrl();
        exposeRequestUrl(requestUrlElement, requestUrl);
        showLoadingAnimation(responseContainer);
        fetch(
          '/api/fetch_response/',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              endpoint: pathDetailedInfo.path,
              requestUrl
            })
          }
        ).then(showResponse.bind(null, responseContainer));
      }

      const dictionaryLabel = event.target.closest('.dictionary-label');
      if (dictionaryLabel !== null)
        dictionaryLabel.parentElement.classList.toggle('collapsed');
      else {
        const collapsed = event.target.closest('.collapsed');
        if (collapsed !== null)
          collapsed.classList.toggle('collapsed');
      }

    });

  }
)();
