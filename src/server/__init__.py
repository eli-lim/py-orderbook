from blacksheep import Application, get

app = Application()


@get("/")
def home(request):
    return "hello"
