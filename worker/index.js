const indexRequestFor = (request) => {
  const url = new URL(request.url);
  const finalSegment = url.pathname.split("/").filter(Boolean).at(-1) || "";

  if (url.pathname.endsWith("/")) {
    url.pathname += "index.html";
  } else if (!finalSegment.includes(".")) {
    url.pathname += "/index.html";
  } else {
    return null;
  }

  return new Request(url, request);
};

export default {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);

    if (response.status !== 404 || !["GET", "HEAD"].includes(request.method)) {
      return response;
    }

    const indexRequest = indexRequestFor(request);
    return indexRequest ? env.ASSETS.fetch(indexRequest) : response;
  },
};
