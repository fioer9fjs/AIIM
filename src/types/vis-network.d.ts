declare module 'vis-network/standalone' {
  export class Network {
    constructor(container: HTMLElement, data: any, options?: any);
    destroy(): void;
    on(event: string, callback: (params: any) => void): void;
    fit(options?: any): void;
    cluster(options?: any): void;
    openCluster(clusterId: string): void;
    isCluster(nodeId: any): boolean;
    body: {
      nodes: Record<string, any>;
    };
  }

  export class DataSet<T> {
    constructor(data?: T[]);
    add(data: T | T[]): void;
    update(data: T | T[]): void;
    remove(id: any): void;
    get(id?: any): any;
  }

  export interface Options {
    nodes?: any;
    edges?: any;
    physics?: any;
    interaction?: any;
    [key: string]: any;
  }

  export interface Node {
    id?: string | number;
    label?: string;
    title?: string;
    shape?: string;
    size?: number;
    color?: any;
    font?: any;
    shadow?: any;
    [key: string]: any;
  }

  export interface Edge {
    id?: string | number;
    from?: string | number;
    to?: string | number;
    label?: string;
    arrows?: any;
    color?: any;
    dashes?: boolean;
    font?: any;
    width?: number;
    [key: string]: any;
  }
}
