class CLIArgument {
    key;
    display_name;
    type;
    value;
    default_value;

    constructor(key, display_name, type, value, default_value) {
        this.key = key;
        this.display_name = display_name;
        this.type = type;
        this.value = value;
        this.default_value = default_value;
    }

    setValue(value) {
        if (value === undefined) {
            this.setValue(null);
        }
        this.value = value;
    }

    static fromJSON(arg) {
        return new CLIArgument(arg.key, arg.display_name, arg.type, undefined, arg.default_value);
    }
}