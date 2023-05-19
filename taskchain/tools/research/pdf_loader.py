from langchain.schema import Document

def load_local(web_path, storage_dir = "C:\\Users\\Lukasz\\Documents\\aivault"):
    import requests, time
    from pathlib import Path

    """Load documents."""
    r = requests.get(web_path)

    file_path = Path(storage_dir) / f"{time.strftime('%Y%m%d-%H%M%S')}.pdf"
    file = open(file_path, "wb")
    file.write(r.content)
    file.close()
    return str(file_path)



def pdf_loader_wrapper(func):
    from fitz import FileDataError
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileDataError:
            print("FileDataError while loading file.")
            web_path = args[0] if len(args) > 0 else kwargs["file_path"]
            file_path = load_local(web_path)
            print(f"Loaded file localy to path :{file_path}")
            if len(args) > 0:
                args = [file_path, *args[1:]]
            else:
                kwargs["file_path"] = file_path
            res = func(*args, **kwargs)
            # update metadata to contain the web url
            for doc in res:
                doc.metadata["source"] = web_path
            return res

    return inner


@pdf_loader_wrapper
def load_pdf_documents_from_url(url, **kwargs) -> list[Document]:
    from langchain.document_loaders import PyMuPDFLoader
    loader = PyMuPDFLoader(url)
    return loader.load(**kwargs)