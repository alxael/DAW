async function filter() {
  const formElement = document.forms.filterForm;
  const formData = new FormData(formElement);

  const response = await fetch(productsListUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
    body: formData,
  }).then((data) => data.json());

  $("#products-list").empty();
  for (const product of response.products) {
    const productCard = $("<div></div>").addClass("card product-card");

    const cardBody = $("<div></div>").addClass("card-body");

    const cardTitle = $("<h4></h4>").text(product.name).addClass("card-title");
    cardBody.append(cardTitle);

    const cardUuid = $("<h6></h6>")
      .text(product.uuid)
      .addClass("card-subtitle text-muted");
    cardBody.append(cardUuid);

    const categoryTagList = $("<div></div>");
    for (const category of product.categories) {
      const categoryTag = $("<span></span>")
        .text(category.name)
        .addClass("badge bg-primary mx-1");
      categoryTagList.append(categoryTag);
    }
    cardBody.append(categoryTagList);

    productCard.append(cardBody);

    $("#products-list").append(productCard);
  }
  return true;
}

filter();
